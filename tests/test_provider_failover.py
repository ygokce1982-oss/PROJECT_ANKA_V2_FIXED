"""Offline contract checks for the prioritized read-only provider fallback chain."""

import unittest
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

from core.providers.provider_manager import ProviderFailoverError, ProviderManager


def provider(*, data=None, valid=True, error=None):
    item = Mock()
    if error is not None:
        item.fetch.side_effect = error
    else:
        item.fetch.return_value = data
    item.validate.return_value = valid
    return item


class ProviderFailoverTests(unittest.TestCase):
    def test_primary_success_does_not_consume_fallback(self):
        manager = ProviderManager()
        first = provider(data={"price": 12.5})
        second = provider(data={"price": 13.0})
        manager.register_provider("primary", first)
        manager.register_provider("fallback", second)
        result = manager.fetch_with_failover(["primary", "fallback"])
        self.assertEqual(result.provider, "primary")
        self.assertEqual(result.data["price"], 12.5)
        self.assertEqual([a.status for a in result.attempts], ["success"])
        second.fetch.assert_not_called()

    def test_primary_exception_uses_fallback_without_secret_leak(self):
        manager = ProviderManager()
        first = provider(error=RuntimeError("API_KEY_DO_NOT_LOG"))
        second = provider(data={"price": 13.0})
        manager.register_provider("primary", first)
        manager.register_provider("fallback", second)
        result = manager.fetch_with_failover(["primary", "fallback"])
        self.assertEqual(result.provider, "fallback")
        self.assertEqual([a.reason for a in result.attempts], ["RuntimeError", ""])
        self.assertNotIn("API_KEY_DO_NOT_LOG", repr(result))

    def test_invalid_and_empty_data_try_next_source(self):
        manager = ProviderManager()
        empty = provider(data={})
        invalid = provider(data={"price": -1.0}, valid=False)
        good = provider(data={"price": 12.0})
        for name, item in (("empty", empty), ("invalid", invalid), ("good", good)):
            manager.register_provider(name, item)
        result = manager.fetch_with_failover(["empty", "invalid", "good"])
        self.assertEqual(result.provider, "good")
        self.assertEqual([a.status for a in result.attempts], ["failed", "failed", "success"])
        empty.validate.assert_not_called()

    def test_both_fail_raise_explicit_sanitized_error(self):
        manager = ProviderManager()
        manager.register_provider("primary", provider(error=OSError("secret-value")))
        manager.register_provider("backup", provider(data={"price": -1}, valid=False))
        with self.assertRaises(ProviderFailoverError) as context:
            manager.fetch_with_failover(["primary", "backup"])
        self.assertEqual(len(context.exception.attempts), 2)
        self.assertEqual([a.reason for a in context.exception.attempts], ["OSError", "ValueError"])
        self.assertNotIn("secret-value", str(context.exception))

    def test_missing_provider_is_traceable_and_skipped(self):
        manager = ProviderManager()
        manager.register_provider("backup", provider(data={"price": 99}))
        result = manager.fetch_with_failover(["not_registered", "backup"])
        self.assertEqual(result.provider, "backup")
        self.assertEqual(result.attempts[0].reason, "NOT_REGISTERED")

    def test_no_valid_registered_provider_fails_closed(self):
        manager = ProviderManager()
        with self.assertRaises(ProviderFailoverError):
            manager.fetch_with_failover(["not_registered"])

    def test_invalid_priority_rejected_before_fetch(self):
        manager = ProviderManager()
        mock = provider(data={"price": 99})
        manager.register_provider("primary", mock)
        for priority in ([], ["primary", "primary"], ["primary", ""]):
            with self.subTest(priority=priority), self.assertRaises(ValueError):
                manager.fetch_with_failover(priority)
        mock.fetch.assert_not_called()

    def test_registration_behavior_unchanged(self):
        manager = ProviderManager()
        mock = provider(data={"price": 99})
        manager.register_provider("primary", mock)
        self.assertEqual(manager.list_providers(), ["primary"])
        self.assertIs(manager.get_provider("primary"), mock)
        manager.remove_provider("primary")
        self.assertEqual(manager.list_providers(), [])

    def test_scalar_priority_and_invalid_acceptance_fail_before_fetch(self):
        manager = ProviderManager()
        item = provider(data={"price": 99})
        manager.register_provider("p", item)
        for priority in ("p", b"p", None, ["p", 1]):
            with self.subTest(priority=priority), self.assertRaises(ValueError):
                manager.fetch_with_failover(priority)
        with self.assertRaises(ValueError):
            manager.fetch_with_failover(["p"], acceptance=True)
        item.fetch.assert_not_called()

    def test_consumer_rejection_or_exception_advances_chain(self):
        for raises in (False, True):
            with self.subTest(raises=raises):
                manager = ProviderManager()
                manager.register_provider("old", provider(data={"age": 99}))
                manager.register_provider("new", provider(data={"age": 1}))
                calls = []
                def accept(data):
                    calls.append(data["age"])
                    if data["age"] == 99 and raises:
                        raise RuntimeError("private-provider-detail")
                    return data["age"] < 2
                result = manager.fetch_with_failover(["old", "new"], acceptance=accept)
                self.assertEqual(result.provider, "new")
                self.assertEqual(calls, [99, 1])
                self.assertNotIn("private-provider-detail", repr(result.attempts))

    def test_validator_and_consumer_must_explicitly_accept(self):
        for provider_result, consumer_result in ((1, True), (True, 1)):
            with self.subTest(provider_result=provider_result, consumer_result=consumer_result):
                manager = ProviderManager()
                manager.register_provider("p", provider(data={"price": 10}, valid=provider_result))
                with self.assertRaises(ProviderFailoverError):
                    manager.fetch_with_failover(["p"], acceptance=lambda data: consumer_result)

    def test_all_empty_payload_shapes_skip_validation(self):
        for value in (None, "", b"", [], {}, (), set()):
            with self.subTest(value=value):
                manager = ProviderManager()
                empty = provider(data=value)
                manager.register_provider("empty", empty)
                manager.register_provider("good", provider(data={"price": 1}))
                self.assertEqual(manager.fetch_with_failover(["empty", "good"]).provider, "good")
                empty.validate.assert_not_called()

    def test_result_repr_excludes_raw_payload(self):
        manager = ProviderManager()
        payload = {"price": 10, "detail": "private-payload-marker"}
        manager.register_provider("p", provider(data=payload))
        result = manager.fetch_with_failover(["p"])
        self.assertIs(result.data, payload)
        self.assertNotIn("private-payload-marker", repr(result))

    def test_shared_provider_calls_do_not_overlap(self):
        manager = ProviderManager()
        entered = threading.Event()
        release = threading.Event()
        second_fetch = threading.Event()
        second_started = threading.Event()
        state_lock = threading.Lock()
        calls = []
        def fetch():
            with state_lock:
                calls.append(len(calls)+1)
                number = len(calls)
            if number == 1:
                entered.set()
                if not release.wait(3):
                    raise RuntimeError("test-release-timeout")
            else:
                second_fetch.set()
            return {"price": number}
        item = provider(data={"price": 1})
        item.fetch.side_effect = fetch
        manager.register_provider("shared", item)
        def second():
            second_started.set()
            return manager.fetch_with_failover(["shared"])
        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(manager.fetch_with_failover, ["shared"])
            try:
                self.assertTrue(entered.wait(2))
                other = executor.submit(second)
                self.assertTrue(second_started.wait(2))
                self.assertFalse(second_fetch.wait(0.05))
            finally:
                release.set()
            self.assertEqual(first.result(timeout=2).data, {"price": 1})
            self.assertEqual(other.result(timeout=2).data, {"price": 2})
        self.assertEqual(calls, [1, 2])

    def test_registry_removal_waits_for_active_fetch(self):
        manager = ProviderManager()
        entered = threading.Event()
        release = threading.Event()
        removal_started = threading.Event()
        removed = threading.Event()
        def fetch():
            entered.set()
            if not release.wait(3):
                raise RuntimeError("test-release-timeout")
            return {"price": 10}
        item = provider(data={"price": 10})
        item.fetch.side_effect = fetch
        manager.register_provider("p", item)
        def remove():
            removal_started.set()
            manager.remove_provider("p")
            removed.set()
        with ThreadPoolExecutor(max_workers=2) as executor:
            future = executor.submit(manager.fetch_with_failover, ["p"])
            try:
                self.assertTrue(entered.wait(2))
                removal = executor.submit(remove)
                self.assertTrue(removal_started.wait(2))
                self.assertFalse(removed.wait(0.05))
            finally:
                release.set()
            self.assertEqual(future.result(timeout=2).provider, "p")
            removal.result(timeout=2)
        self.assertEqual(manager.list_providers(), [])


    def test_real_matriks_adapter_can_be_primary_without_network(self):
        from core.providers.matriks_provider import MatriksProvider

        session = Mock()
        response = Mock()
        response.json.return_value = [{
            "time": 1628542800000, "open": 9.12, "high": 9.21,
            "low": 9.04, "close": 9.11,
            "totalQuantity": 168545356, "volume": 1538559735.08,
        }]
        session.get.return_value = response
        primary = MatriksProvider(
            token="fake-local-token", session=session,
            symbol="GARAN", start="2021-08-10", end="2021-08-12"
        )
        backup = provider(data=[{"close": 10.0}])
        manager = ProviderManager()
        manager.register_provider("matriks", primary)
        manager.register_provider("backup", backup)
        result = manager.fetch_with_failover(["matriks", "backup"])
        self.assertEqual(result.provider, "matriks")
        self.assertEqual(result.data[0]["close"], 9.11)
        backup.fetch.assert_not_called()
        session.get.assert_called_once()

    def test_real_matriks_adapter_failure_triggers_safe_backup(self):
        from requests.exceptions import Timeout
        from core.providers.matriks_provider import MatriksProvider

        session = Mock()
        session.get.side_effect = Timeout("token_secret_never_expose")
        primary = MatriksProvider(
            token="fake-local-token", session=session,
            symbol="GARAN", start="2021-08-10", end="2021-08-12"
        )
        backup = provider(data=[{"close": 10.0}])
        manager = ProviderManager()
        manager.register_provider("matriks", primary)
        manager.register_provider("backup", backup)
        result = manager.fetch_with_failover(["matriks", "backup"])
        self.assertEqual(result.provider, "backup")
        self.assertEqual(result.attempts[0].reason, "Timeout")
        self.assertNotIn("token_secret_never_expose", repr(result))


if __name__ == "__main__":
    unittest.main()

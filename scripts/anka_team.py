"""ANKA Finans local delivery team: persistent, read-only AI planning tasks.

The agents produce recommendations, not code changes or financial orders.
All generated claims require human verification before implementation.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.agent_hub import AgentHub
from core.agent_hub.agent_registry import AgentRegistry
from core.agent_hub.adapters.ollama_adapter import OllamaAdapter
from core.agent_hub.models import TaskStatus
from core.agent_hub.task_store import TaskStore

BATCH = "ANKA-TEAM-20261009"
ROLE_MODELS = {
    "researcher": "gemma3:1b",
    "coder": "qwen2.5-coder:1.5b",
    "reviewer": "gemma3:1b",
    "analyst": "gemma3:1b",
}
TASKS = (
    ("researcher", "Veri kaynaklari ve lisans riskleri", 140,
     "Mevcut prototipin BIST/XU100, altin ve kripto veri eksiklerini incele. "
     "Lisans, gecikme, kaynak yedekliligi ve hata durumlari icin ilk 3 adimi oner."),
    ("coder", "En kucuk uygulanabilir teknik dilim", 130,
     "Kod tabanina uygun, 1-3 gunluk uygulanabilir bir gelistirme dilimi oner. "
     "Dosya adlari, kabul kriterleri ve testleri somutlastir. Kod calistirdigini iddia etme."),
    ("reviewer", "Mimari ve guvenlik denetimi", 120,
     "Agent Hub, veri saglayicilari ve UI icin kritik riskleri belirle. "
     "Otonom kod yazma, emir gonderme ve kimlik bilgilerine erisim icin onay kapilari oner."),
    ("analyst", "Hizlandirilmis teslim plani", 110,
     "Ilk kullanilabilir surum icin oncelikleri, bagimliliklari ve dogrulanabilir "
     "kabul kriterlerini belirle. Kesin tarih ve garanti uydurma."),
)


def project_snapshot(root: Path = ROOT) -> str:
    """Share only selected public project documentation with local models."""
    parts = []
    for relative in ("PROJECT_STATUS.md", "ROADMAP.md", "docs/ARCHITECTURE.md"):
        path = root / relative
        if path.is_file():
            parts.append(f"[{relative}]\n{path.read_text(encoding='utf-8', errors='replace')[:1400]}")
    return "\n\n".join(parts)[:4200]


def build_registry(base_url: str, model: str | None = None, *, cpu_only: bool = False) -> AgentRegistry:
    registry = AgentRegistry()
    for role, default_model in ROLE_MODELS.items():
        registry.register(
            f"local-{role}",
            OllamaAdapter(
                name=f"local-{role}",
                role=role,
                model=model or default_model,
                base_url=base_url,
                num_gpu=0 if cpu_only else None,
            ),
        )
    return registry


def available_models(base_url: str) -> set[str]:
    session = requests.Session()
    session.trust_env = False
    try:
        response = session.get(f"{base_url.rstrip('/')}/api/tags", timeout=5)
        response.raise_for_status()
        payload = response.json()
        return {
            item["name"]
            for item in payload.get("models", [])
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }
    finally:
        session.close()


def seed_tasks(hub: AgentHub, snapshot: str) -> list[int]:
    """Idempotently enqueue one read-only task per role."""
    existing = {task.title for task in hub.task_store.list_tasks()}
    created = []
    for role, name, priority, instruction in TASKS:
        title = f"{BATCH}: {name}"
        if title in existing:
            continue
        description = (
            "Turkce, kisa ve denetlenebilir yanit ver. "
            "Yalnizca verilen dokumanlari degerlendir. "
            "Dis kaynaklara eristigini, test yaptigini veya kod degistirdigini iddia etme. "
            "Emir, odeme, dosya degisikligi veya komut calistirma YAPMA. "
            "En fazla 5 madde yaz.\n\n"
            f"GOREV: {instruction}\n\nMEVCUT PROJE:\n{snapshot}"
        )
        task = hub.enqueue_task(
            title=title,
            description=description,
            role=role,
            priority=priority,
            max_attempts=1,
            requires_approval=False,
        )
        created.append(task.id)
    return created


def write_report(store: TaskStore, path: Path) -> None:
    """Keep AI proposals explicitly separate from verified implementation."""
    lines = [
        "# ANKA Finans - Yerel Ajan Ekibi Raporu",
        "",
        "Bu rapor yerel modellerin ONERILERINI icerir; tamamlanmis kod, "
        "lisans kontrolu veya dogrulanmis canli piyasa verisi degildir.",
        "",
    ]
    for task in store.list_tasks():
        if not task.title.startswith(BATCH):
            continue
        lines.extend(
            [
                f"## {task.title}",
                f"- Rol: {task.role}",
                f"- Durum: {task.status.value}",
                f"- Deneme: {task.attempts}/{task.max_attempts}",
                "",
                task.result or task.error or "Henuz sonuc yok.",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ANKA Finans yerel ajan ekibi")
    parser.add_argument("command", choices=("status", "seed", "run", "kickoff", "report", "retry"))
    parser.add_argument("--model", help="Tum roller icin mevcut Ollama modeli")
    parser.add_argument("--cpu-only", action="store_true", help="Ollama modellerini yalnizca CPU ile calistir")
    parser.add_argument("--base-url", default=os.getenv("ANKA_OLLAMA_URL", "http://localhost:11434"))
    parser.add_argument("--max-tasks", type=int, default=4)
    parser.add_argument("--db", default=str(ROOT / "logs" / "anka_team.db"))
    args = parser.parse_args(argv)

    if args.max_tasks < 1:
        parser.error("--max-tasks pozitif olmali")

    store = TaskStore(db_path=args.db)
    registry = build_registry(args.base_url, args.model, cpu_only=args.cpu_only)
    hub = AgentHub(
        task_store=store,
        registry=registry,
        adapter_timeout_seconds=180,
        lease_seconds=240,
        worker_id="anka-local-delivery-team",
    )

    if args.command == "status":
        try:
            models = available_models(args.base_url)
            for role, default in ROLE_MODELS.items():
                selected = args.model or default
                print(f"{role}: {selected} - {'yuklu (calisma dogrulanmadi)' if selected in models else 'model eksik'}")
        except (requests.RequestException, ValueError) as exc:
            print(f"Ollama baglanti hatasi: {exc}")
            return 1
        for task in store.list_tasks():
            if task.title.startswith(BATCH):
                print(f"#{task.id}: {task.role}: {task.status.value}")
        return 0

    if args.command == "retry":
        retried = 0
        for task in store.list_tasks(statuses=[TaskStatus.FAILED]):
            if task.title.startswith(BATCH):
                store.update_task(
                    task.id, status=TaskStatus.QUEUED, attempts=0, error="", clear_lock=True
                )
                retried += 1
        print(f"Yeniden kuyruga alinan gorev: {retried}")
        return 0

    if args.command in ("seed", "kickoff"):
        created = seed_tasks(hub, project_snapshot())
        print(f"Kuyruga eklenen yeni gorev: {len(created)}; kimlikler: {created}")

    if args.command in ("run", "kickoff"):
        try:
            models = available_models(args.base_url)
        except (requests.RequestException, ValueError) as exc:
            print(f"Ollama kullanilamiyor: {exc}")
            return 1
        missing = sorted({args.model or model for model in ROLE_MODELS.values()} - models)
        if missing:
            print(f"Eksik yerel modeller: {', '.join(missing)}")
            return 1
        failed = False
        for _ in range(args.max_tasks):
            result = hub.run_next()
            if result is None:
                break
            print(f"Gorev #{result.task_id}: {result.status.value}")
            if result.error:
                print(f"Hata: {result.error}")
            if not result.success:
                failed = True
        write_report(store, ROOT / "docs" / "TEAM_REPORT_20261009.md")
        print("Rapor: docs/TEAM_REPORT_20261009.md")
        return 1 if failed else 0

    if args.command == "report":
        write_report(store, ROOT / "docs" / "TEAM_REPORT_20261009.md")
        print("Rapor: docs/TEAM_REPORT_20261009.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

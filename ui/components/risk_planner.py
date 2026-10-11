"""User-entered hypothetical risk analysis; no providers or order actions."""

from __future__ import annotations

import math

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.trade_risk import calculate_risk_plan


class RiskPlannerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plan = None
        layout = QVBoxLayout(self)
        notice = QLabel(
            "VARSAYIMSAL LONG / SHORT risk planı · Çevrimdışı · Emir göndermez.\n"
            "Fiyatları kendiniz girin. Tüm parasal değerler aynı para biriminde "
            "olmalıdır. Kaldıraç kullanılmaz. Maksimum kayıp, girilen stop ve "
            "komisyona göre hesaplanır; gerçekleşecek kayıp garantisi değildir."
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        form = QFormLayout()
        self.side = QComboBox()
        self.side.addItems(["LONG", "SHORT"])
        form.addRow("Varsayımsal yön", self.side)
        self.inputs = {}
        self.labels = {
            "entry": "Giriş fiyatı",
            "stop": "Stop fiyatı",
            "target": "Hedef fiyatı",
            "equity": "Sermaye",
            "risk_percent": "Risk (%) · 0'dan büyük, en fazla 10",
            "fee_percent": "Tek yön komisyon (%) · 0–5",
            "lot_step": "Lot adımı",
        }
        for key, label in self.labels.items():
            field = QLineEdit()
            field.setPlaceholderText("Elle girin · ondalık ayırıcı nokta veya virgül")
            self.inputs[key] = field
            form.addRow(label, field)
            field.textChanged.connect(self.clear_result)
        layout.addLayout(form)
        self.calculate_button = QPushButton("Varsayımsal planı hesapla")
        self.calculate_button.clicked.connect(self.calculate)
        layout.addWidget(self.calculate_button)
        self.status = QLabel("Hesaplama için tüm alanları doldurun.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.results = {}
        results_form = QFormLayout()
        for key, label in (
            ("quantity", "Hesaplanan lot miktarı"),
            ("risk_budget", "Risk bütçesi"),
            ("potential_loss", "Stop senaryosunda maksimum kayıp · komisyon dahil"),
            ("reward_risk_ratio", "Ödül / risk"),
        ):
            value = QLabel("—")
            self.results[key] = value
            results_form.addRow(label, value)
        layout.addLayout(results_form)
        self.side.currentTextChanged.connect(self.clear_result)

    def clear_result(self, *_):
        self.plan = None
        for label in self.results.values():
            label.setText("—")
        self.status.setText("Girdiler değişti; varsayımsal planı yeniden hesaplayın.")

    def _values(self):
        values = {}
        for key, field in self.inputs.items():
            text = field.text().strip().replace(",", ".")
            try:
                value = float(text)
            except ValueError:
                raise ValueError(f"{self.labels[key]}: geçerli bir sayı girin.") from None
            if not math.isfinite(value):
                raise ValueError(f"{self.labels[key]}: sonlu bir sayı girin.")
            if key == "fee_percent":
                if not 0 <= value <= 5:
                    raise ValueError("Komisyon %0 ile %5 arasında olmalıdır.")
            elif value <= 0:
                raise ValueError(f"{self.labels[key]}: sıfırdan büyük olmalıdır.")
            if key == "risk_percent" and value > 10:
                raise ValueError("Risk oranı %10'u aşamaz.")
            values[key] = value
        return values

    def calculate(self, *_):
        self.clear_result()
        try:
            values = self._values()
            side = self.side.currentText()
            entry, stop, target = (values[key] for key in ("entry", "stop", "target"))
            if side == "LONG" and not stop < entry < target:
                raise ValueError("LONG için stop < giriş < hedef olmalıdır.")
            if side == "SHORT" and not target < entry < stop:
                raise ValueError("SHORT için hedef < giriş < stop olmalıdır.")
            plan = calculate_risk_plan(
                side=side, entry=entry, stop=stop, target=target,
                equity=values["equity"],
                risk_fraction=values["risk_percent"] / 100,
                fee_rate=values["fee_percent"] / 100,
                lot_step=values["lot_step"],
            )
        except ValueError as error:
            message = str(error)
            if message == "Sermaye ve risk sinirlariyla asgari lot alinamiyor":
                message = (
                    "Sermaye veya risk bütçesi bir lot adımı için yetersiz. "
                    "Girdileri kontrol edin."
                )
            self.status.setText("Plan hesaplanamadı: " + message)
            return
        self.plan = plan
        for key, label in self.results.items():
            label.setText(format(getattr(plan, key), ".12g"))
        message = "Varsayımsal plan hesaplandı. Canlı bağlantı ve emir iletimi yok."
        if plan.potential_reward <= 0:
            message += " Komisyon sonrası hedef ödülü sıfır veya negatif."
        self.status.setText(message)

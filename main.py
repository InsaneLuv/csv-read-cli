import json
from dataclasses import dataclass, fields, asdict
from pathlib import Path
from typing import Type, Dict, Any, List

import fire


@dataclass
class ReportBase:
    id: str
    email: str
    name: str
    department: str
    hours_worked: int


@dataclass
class ReportPayout(ReportBase):
    pay: int
    payout: int


class BaseReportGenerator:
    model: Type[ReportBase]

    def __init__(self, files: List[str], report: str):
        self.files = files
        self.report = report

    def _str_to_path(self, fp) -> Path | None:
        path = Path(fp)
        if path.exists():
            return path
        return None

    def _except_not_exists(self) -> list[Path]:
        exists = []
        for fp in self.files:
            file_path = self._str_to_path(fp)
            if file_path:
                exists.append(file_path)
        return exists

    def run(self):
        data_list: List[Dict[str, Any]] = []
        base_fields = {f.name for f in fields(ReportBase)}
        exists_files = self._except_not_exists()
        for path in exists_files:
            lines = path.read_text(encoding="utf-8").splitlines()
            if not lines:
                continue
            header = lines[0].split(",")
            fixed_cols = [col for col in header if col in base_fields]
            pay_idx = next((i for i, col in enumerate(header) if col not in base_fields), None)
            hours_idx = header.index("hours_worked") if "hours_worked" in header else None
            field_names = [f.name for f in fields(self.model)]

            for line in lines[1:]:
                if not line.strip():
                    continue
                values = line.split(",")
                base_kwargs: Dict[str, Any] = {}
                for col in fixed_cols:
                    idx = header.index(col)
                    val = values[idx]
                    if col == "hours_worked":
                        try:
                            base_kwargs[col] = int(val)
                        except ValueError:
                            base_kwargs[col] = 0
                    else:
                        base_kwargs[col] = val
                extra_kwargs = self.compute_extra(values, header, base_kwargs, pay_idx, hours_idx)
                record_kwargs = {**base_kwargs, **extra_kwargs}
                record = self.model(**record_kwargs)
                data_list.append(asdict(record))
                row = [str(getattr(record, name)) for name in field_names]
                print(row)  # для тестов

            json_path = Path(f"{self.report}.json")
            with json_path.open("w", encoding="utf-8") as f:
                json.dump(data_list, f, ensure_ascii=False, indent=2)

    def compute_extra(self, values: List[str], header: List[str], base_kwargs: Dict[str, Any], pay_idx: Any,
                      hours_idx: Any) -> Dict[str, Any]:
        return {}


class PayoutReportGenerator(BaseReportGenerator):
    model = ReportPayout

    def compute_extra(self, values: List[str], header: List[str], base_kwargs: Dict[str, Any], pay_idx: Any,
                      hours_idx: Any) -> Dict[str, Any]:
        if pay_idx is not None:
            try:
                pay_val = int(values[pay_idx])
            except (ValueError, TypeError):
                pay_val = 0
        else:
            pay_val = 0
        hours_val = base_kwargs.get("hours_worked", 0)
        payout_val = hours_val * pay_val
        return {"pay": pay_val, "payout": payout_val}


GENERATORS: Dict[str, Type[BaseReportGenerator]] = {
    "payout": PayoutReportGenerator,
    ## Сюда дописывать новые репорты
}


def report_func(*files: str, report: str, report_type: str = "payout"):
    if report_type not in GENERATORS:
        print(f"Невозможно сформировать отчёт '{report_type}'. Доступные отчёты: {list(GENERATORS.keys())}")
        return
    generator = GENERATORS[report_type](list(files), report)
    generator.run()


if __name__ == "__main__":
    fire.Fire(report_func)

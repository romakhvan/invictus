"""
Мониторинг создания чеков web-kassa по всем клубам.
Анализирует транзакции и показывает статистику по каждому клубу.
"""

import allure
import json
import csv
import io
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict
from src.utils.repository_helpers import get_collection




def _error_short(error_text: str) -> str:
    et = error_text.lower()
    if "автономном режиме" in et or "72" in et:
        return "ОФД offline > 72h"
    if "лицензи" in et:
        return "нет лицензии"
    if "сумма" in et and ("меньше" in et or "не может" in et):
        return "сумма < 0"
    if "безналичной" in et and "больше" in et:
        return "безнал > итого"
    if "отменена" in et:
        return "транзакция отменена"
    return error_text[:60]


def _get_recommendation(error_text: str) -> str:
    et = error_text.lower()
    if "автономном режиме" in et or "офд" in et or "72" in et:
        return "Проверить подключение кассы к ОФД"
    if "лицензи" in et:
        return "Проверить статус лицензии кассы в личном кабинете ОФД"
    if "сумма" in et and ("меньше" in et or "не может" in et):
        return "Проверить логику расчёта суммы транзакции (возможно отрицательная скидка)"
    if "безналичной" in et and "больше" in et:
        return "Проверить расчёт безналичной части оплаты"
    if "отменена" in et:
        return "Транзакция отменена клиентом — проверить логику повторных попыток"
    return "Проверить логи кассового оборудования"


def _club_breakdown_to_html(clubs_data: list) -> str:
    sections = []
    for club in clubs_data:
        th_cells = "".join(
            f"<th style='text-align:left;padding:4px 8px;background:#f0f0f0'>{h}</th>"
            for h in ["Дата", "Transaction ID", "Сумма", "Ошибка"]
        )
        trs = []
        for e in club["examples"]:
            price_fmt = f"{e['price']:,}".replace(",", " ") + " тг"
            cells = [e["date"], e["trans_id"], price_fmt, e["error_text"]]
            trs.append("<tr>" + "".join(
                f"<td style='padding:3px 8px;font-size:12px'>{c}</td>" for c in cells
            ) + "</tr>")
        table = (
            f'<table border="1" cellpadding="0" cellspacing="0" '
            f'style="border-collapse:collapse;margin-top:6px">'
            f'<thead><tr>{th_cells}</tr></thead>'
            f'<tbody>{"".join(trs)}</tbody></table>'
        )
        sections.append(
            f'<div style="margin-bottom:20px;font-family:monospace">'
            f'<h3 style="margin:0 0 4px">{club["name"]}</h3>'
            f'<p style="margin:2px 0">Всего ошибок: <b>{club["total_errors"]}</b>'
            f' &nbsp;|&nbsp; Уникальных типов: {club["unique_errors"]}'
            f' &nbsp;|&nbsp; Последняя: {club["last_date"]}</p>'
            f'<p style="margin:2px 0">Основная причина: <i>{club["main_error"]}</i></p>'
            f'<p style="margin:2px 0;color:#555">Рекомендация: {club["recommendation"]}</p>'
            f'{table}</div>'
        )
    body = "".join(sections) or "<p>Нет ошибочных транзакций</p>"
    return f'<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>{body}</body></html>'


def _to_csv(rows: list) -> str:
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def _short_club_name(name: str) -> str:
    for prefix in ("Invictus GO ", "Invictus Fitness ", "Invictus Girls "):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def _error_types_to_html(rows: list) -> str:
    headers = ["Тип ошибки", "Кол-во", "Клубы", "productType", "source", "instalmentType"]
    th = "".join(f"<th style='text-align:left;padding:6px 10px'>{h}</th>" for h in headers)
    trs = []
    for r in rows:
        cells = [
            r["error_text"],
            f"<b>{r['count']}</b>",
            ", ".join(sorted(r["clubs"])),
            ", ".join(sorted(r["productTypes"] - {"—"})) or "—",
            ", ".join(sorted(r["sources"] - {"—"})) or "—",
            ", ".join(sorted(r["instalmentTypes"] - {"—"})) or "—",
        ]
        trs.append(
            "<tr>" +
            "".join(f"<td style='padding:5px 10px;vertical-align:top'>{c}</td>" for c in cells) +
            "</tr>"
        )
    style = "border-collapse:collapse;font-family:monospace;font-size:13px"
    table = (
        f'<table border="1" cellpadding="0" cellspacing="0" style="{style}">'
        f'<thead style="background:#f0f0f0"><tr>{th}</tr></thead>'
        f'<tbody>{"".join(trs)}</tbody></table>'
    )
    return f'<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>{table}</body></html>'


def _clubs_errors_summary_to_html(rows: list) -> str:
    headers = ["Клуб", "Кол-во", "Ошибка", "Последняя транзакция"]
    th = "".join(f"<th style='text-align:left;padding:6px 10px'>{h}</th>" for h in headers)
    trs = []
    for r in rows:
        cells = [
            r["club"],
            f"<b>{r['error_count']}</b>",
            r["error_text"],
            f"{r['last_transaction_id']}<br><small>{r['last_transaction_date']}</small>",
        ]
        trs.append(
            "<tr>" +
            "".join(f"<td style='padding:5px 10px;vertical-align:top'>{c}</td>" for c in cells) +
            "</tr>"
        )
    style = "border-collapse:collapse;font-family:monospace;font-size:13px"
    table = (
        f'<table border="1" cellpadding="0" cellspacing="0" style="{style}">'
        f'<thead style="background:#f0f0f0"><tr>{th}</tr></thead>'
        f'<tbody>{"".join(trs)}</tbody></table>'
    )
    return f'<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>{table}</body></html>'


@allure.feature('WebKassa Monitoring')
@allure.story('Receipt Creation Status')
@allure.title('Мониторинг создания чеков WebKassa по клубам')
@allure.description('Анализирует транзакции за указанный период (--period-days) и показывает статистику создания чеков по каждому клубу')
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag('backend', 'webkassa', 'monitoring', 'receipts')
@allure.link("https://docs.google.com/spreadsheets/d/1zE_eUYsGQXvJQOM3FnOc83O2mt5pZT8-SvJwQ2YeCnA/edit?gid=0#gid=0")
def test_webkassa_status_by_clubs(db, period_days):
    """
    Анализирует создание чеков по всем клубам за указанный период.
    Показывает статистику по каждому клубу и итоговую оценку.
    """
    # ── Шаг 1: Сбор данных ────────────────────────────────────────────────
    with allure.step("Сбор данных"):
        now = datetime.now()
        days_ago = now - timedelta(days=period_days)

        allure.attach(
            f"Период анализа: последние {period_days} дней\n"
            f"Дата запуска: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            name="Конфигурация теста",
            attachment_type=allure.attachment_type.TEXT
        )
        print("\n" + "=" * 110)
        print("МОНИТОРИНГ СОЗДАНИЯ ЧЕКОВ WEB-KASSA ПО КЛУБАМ")
        print("=" * 110)
        print(f"\nПериод анализа (последние {period_days} дней):")
        print(f"  С: {days_ago.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  По: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        excluded_club_ids = [
            ObjectId("68b8060be664a702920a547d"), # Invictus GO Bishkek
            ObjectId("6480df84f493f6015319936d"), # Invictus GO Baitursynov (shop)
            ObjectId("681e3cfc635290fa6d953b10"), # Invictus Fitness Akbulak Riviera
            ObjectId("683574f3f6c08fc5af1eba6b"), # Invictus GO OXY
            ObjectId("6735ee6836765d003669dc72"), # Invictus GO Aport East
            ObjectId("61e6940c1c5b19780b303507"), # Invictus GO Aqsay
            ObjectId("662238db99337806676947b3"), # Invictus GO Shalyapin
            ObjectId("621875f8a81b6009230607e0"), # Invictus Fitness Sadu
            ObjectId("668687f7ab149a00a04341be"), # Invictus GO Austria
            ObjectId("61ea59bf4360983086b47f3d"), # Invictus Fitness Al-Farabi
            ObjectId("656716180916e102c983dfbe"), # Invictus Girls Nursat
            ObjectId("65144d379928de0202b789f9"), # Invictus Fitness Nursat
            ObjectId("6932d95c3f5fce2f4a89ba9e"), # Invictus GO Arena
            ObjectId("687f521e770a1c01340880c5"), # Invictus Fitness Oral
            ObjectId("690deed030c845004162369c"), # Invictus GO Ualikhanov
            ObjectId("6523f8eb606d2f00fb03b5c6"), # Invictus Fitness Atyrau
            ObjectId("68382801f6c08fc5af1eba9a"), # Invictus GO Raiymbek Batyr
            ObjectId("622127a7097e5c3170553862"), # Invictus Fitness Semey
        ]

        clubs_col = get_collection(db, "clubs")
        excluded_clubs = list(clubs_col.find(
            {"_id": {"$in": excluded_club_ids}},
            {"_id": 1, "name": 1}
        ))
        if excluded_clubs:
            excluded_names = "\n".join([f"- {c['name']}" for c in excluded_clubs])
            allure.attach(
                f"Всего исключенных клубов: {len(excluded_clubs)}\n\n{excluded_names}",
                name="Исключенные клубы",
                attachment_type=allure.attachment_type.TEXT
            )

        transactions_col = get_collection(db, "transactions")
        transactions = list(transactions_col.find({
            "status": "success",
            "created_at": {"$gte": days_ago},
            "isDeleted": False,
            "source": {"$in": ["mobile", "website"]},
            "clubId": {"$exists": True, "$ne": None, "$nin": excluded_club_ids}
        }, {
            "_id": 1,
            "clubId": 1,
            "webKassaIds": 1,
            "price": 1,
            "created_at": 1,
            "productType": 1,
            "source": 1,
            "instalmentType": 1
        }).sort("created_at", -1))

        print(f"\nВсего транзакций за период: {len(transactions)}")
        if not transactions:
            print("Нет транзакций для анализа")
            return

        club_ids = list(set([t["clubId"] for t in transactions]))
        clubs = list(clubs_col.find({"_id": {"$in": club_ids}}, {"_id": 1, "name": 1}))
        club_id_to_name = {club["_id"]: club["name"] for club in clubs}
        print(f"Уникальных клубов: {len(club_ids)}")

        all_webkassa_ids = []
        transaction_to_webkassa = {}
        for trans in transactions:
            wk_ids = trans.get("webKassaIds", [])
            if wk_ids:
                all_webkassa_ids.extend(wk_ids)
                transaction_to_webkassa[trans["_id"]] = wk_ids

        webkassas_col = get_collection(db, "webkassas")
        webkassas = list(webkassas_col.find(
            {"_id": {"$in": all_webkassa_ids}},
            {"_id": 1, "status": 1, "body": 1}
        ))
        webkassa_statuses = {wk["_id"]: wk.get("status", "unknown") for wk in webkassas}
        webkassa_errors = {}
        for wk in webkassas:
            if wk.get("status") == "error":
                body = wk.get("body", [])
                if body and isinstance(body[0], dict):
                    error_text = body[0].get("Text", "")
                    if error_text:
                        webkassa_errors[wk["_id"]] = error_text

        print(f"Найдено чеков в webkassas: {len(webkassas)}, с ошибками: {len(webkassa_errors)}")

    # ── Шаг 2: Анализ транзакций ──────────────────────────────────────────
    with allure.step("Анализ транзакций"):
        error_type_stats = defaultdict(lambda: {
            "count": 0,
            "clubs": set(),
            "productTypes": set(),
            "sources": set(),
            "instalmentTypes": set(),
        })
        all_error_transactions = []
        club_stats = defaultdict(lambda: {
            "name": "",
            "total": 0,
            "with_success_receipts": 0,
            "with_error_receipts": 0,
            "without_receipts": 0,
            "success_examples": [],
            "error_examples": [],
            "empty_examples": [],
            "error_text_counts": defaultdict(int),
        })

        for trans in transactions:
            club_id = trans["clubId"]
            trans_id = trans["_id"]
            club_stats[club_id]["name"] = club_id_to_name.get(club_id, f"Unknown ({club_id})")
            club_stats[club_id]["total"] += 1

            webkassa_ids = trans.get("webKassaIds", [])
            if not webkassa_ids:
                club_stats[club_id]["without_receipts"] += 1
                if len(club_stats[club_id]["empty_examples"]) < 5:
                    club_stats[club_id]["empty_examples"].append({
                        "transaction_id": trans_id,
                        "price": trans.get("price", 0),
                        "created_at": trans.get("created_at"),
                        "productType": trans.get("productType")
                    })
            else:
                has_error = False
                has_success = False
                for wk_id in webkassa_ids:
                    status = webkassa_statuses.get(wk_id, "not_found")
                    if status == "success":
                        has_success = True
                    else:
                        has_error = True

                # Если хотя бы один чек с ошибкой — транзакция считается ошибочной,
                # даже если остальные чеки успешны
                if has_error:
                    club_stats[club_id]["with_error_receipts"] += 1
                    error_texts = [webkassa_errors[wk_id] for wk_id in webkassa_ids if wk_id in webkassa_errors]
                    club_name_full = club_id_to_name.get(club_id, str(club_id))
                    seen_errors = set()
                    for et in error_texts:
                        club_stats[club_id]["error_text_counts"][et] += 1
                        if et not in seen_errors:
                            seen_errors.add(et)
                            error_type_stats[et]["count"] += 1
                            error_type_stats[et]["clubs"].add(_short_club_name(club_name_full))
                            error_type_stats[et]["productTypes"].add(trans.get("productType") or "—")
                            error_type_stats[et]["sources"].add(trans.get("source") or "—")
                            error_type_stats[et]["instalmentTypes"].add(trans.get("instalmentType") or "—")

                    created_at = trans.get("created_at")
                    all_error_transactions.append({
                        "club": club_name_full,
                        "transaction_id": str(trans_id),
                        "price": trans.get("price", 0),
                        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "",
                        "error_text": error_texts[0] if error_texts else "",
                        "productType": trans.get("productType") or "",
                        "source": trans.get("source") or "",
                        "instalmentType": trans.get("instalmentType") or "",
                    })
                    if len(club_stats[club_id]["error_examples"]) < 5:
                        club_stats[club_id]["error_examples"].append({
                            "transaction_id": trans_id,
                            "webkassa_ids": webkassa_ids,
                            "statuses": [webkassa_statuses.get(wk_id, "not_found") for wk_id in webkassa_ids],
                            "error_texts": error_texts,
                            "price": trans.get("price", 0),
                            "created_at": created_at,
                        })
                elif has_success:
                    club_stats[club_id]["with_success_receipts"] += 1

        sorted_clubs_alphabetically = sorted(club_stats.items(), key=lambda x: x[1]["name"])
        sorted_clubs_by_problems = sorted(
            club_stats.items(),
            key=lambda x: (x[1]["with_error_receipts"] + x[1]["without_receipts"], x[1]["total"]),
            reverse=True
        )

        clubs_with_problems = []
        clubs_without_problems = []
        for club_id, stats in sorted_clubs_alphabetically:
            if stats["with_error_receipts"] > 0 or stats["without_receipts"] > 0:
                clubs_with_problems.append((club_id, stats))
            else:
                clubs_without_problems.append((club_id, stats))

        # Таблица клубов с проблемами
        print("\n" + "=" * 110)
        print(f"ТАБЛИЦА 1: КЛУБЫ С ПРОБЛЕМАМИ ({len(clubs_with_problems)} клубов)")
        print("=" * 110)

        total_problems_trans = 0
        total_problems_success = 0
        total_problems_errors = 0
        total_problems_empty = 0

        if clubs_with_problems:
            print(f"\n{'№':<4} {'Клуб':<40} {'Всего':<8} {'Успешн.':<10} {'Ошибки':<10} {'Без чека':<10} {'% Проблем':<10}")
            print("=" * 110)
            for idx, (club_id, stats) in enumerate(clubs_with_problems, start=1):
                total = stats["total"]
                success = stats["with_success_receipts"]
                errors = stats["with_error_receipts"]
                empty = stats["without_receipts"]
                total_problems_trans += total
                total_problems_success += success
                total_problems_errors += errors
                total_problems_empty += empty
                problem_percent = ((errors + empty) / total * 100) if total > 0 else 0
                print(f"{idx:<4} {stats['name'][:38]:<40} {total:<8} {success:<10} {errors:<10} {empty:<10} {problem_percent:>8.1f}%")
            print("=" * 110)
            print(f"{'':>4} {'ИТОГО':<40} {total_problems_trans:<8} {total_problems_success:<10} {total_problems_errors:<10} {total_problems_empty:<10}")
            print("=" * 110)
        else:
            print("\nВсе клубы работают без проблем!")

        total_perfect_trans = sum(s["total"] for _, s in clubs_without_problems)
        total_perfect_success = sum(s["with_success_receipts"] for _, s in clubs_without_problems)

        total_transactions = total_problems_trans + total_perfect_trans
        total_success = total_problems_success + total_perfect_success
        total_errors = total_problems_errors
        total_empty = total_problems_empty

        print("\n" + "=" * 110)
        print("ОБЩАЯ СТАТИСТИКА ПО ВСЕМ КЛУБАМ")
        print("=" * 110)
        print(f"Всего клубов: {len(sorted_clubs_alphabetically)}")
        print(f"  - С проблемами: {len(clubs_with_problems)}")
        print(f"  - Без проблем: {len(clubs_without_problems)}")
        print(f"\nВсего транзакций: {total_transactions}")
        print(f"  - С успешными чеками: {total_success}")
        print(f"  - С ошибочными чеками: {total_errors}")
        print(f"  - Без чеков: {total_empty}")
        print("=" * 110)

        success_rate = (total_success / total_transactions * 100) if total_transactions > 0 else 0
        error_rate = (total_errors / total_transactions * 100) if total_transactions > 0 else 0
        empty_rate = (total_empty / total_transactions * 100) if total_transactions > 0 else 0

        allure.attach(
            f"Всего клубов: {len(sorted_clubs_alphabetically)}\n"
            f"  - С проблемами: {len(clubs_with_problems)}\n"
            f"  - Без проблем: {len(clubs_without_problems)}\n\n"
            f"Всего транзакций: {total_transactions}\n"
            f"  - С успешными чеками: {total_success} ({success_rate:.1f}%)\n"
            f"  - С ошибочными чеками: {total_errors} ({error_rate:.1f}%)\n"
            f"  - Без чеков: {total_empty} ({empty_rate:.1f}%)",
            name="Общая статистика",
            attachment_type=allure.attachment_type.TEXT
        )

        # Примеры ошибочных транзакций
        print("\n" + "=" * 110)
        print("ПРИМЕРЫ ТРАНЗАКЦИЙ С ОШИБОЧНЫМИ ЧЕКАМИ (до 5 на клуб)")
        print("=" * 110)
        error_count = 0
        allure_error_blocks = []
        for club_id, stats in sorted_clubs_by_problems:
            if stats["error_examples"]:
                club_lines = [f"Клуб: {stats['name']} ({stats['with_error_receipts']})"]
                club_info = f"\nКлуб: {stats['name']}\nВсего ошибочных: {stats['with_error_receipts']}\n"
                print(club_info)
                for example in stats["error_examples"]:
                    error_count += 1
                    example_text = [
                        f"  - Transaction: {example['transaction_id']}",
                        f"    WebKassa IDs: {example['webkassa_ids']}",
                        f"    Статусы: {example['statuses']}"
                    ]
                    if example.get('error_texts'):
                        example_text.append("    Тексты ошибок:")
                        for error_text in example['error_texts']:
                            example_text.append(f"      • {error_text}")
                    example_text.append(f"    Сумма: {example['price']} тг")
                    example_text.append(f"    Дата: {example['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                    print("\n".join(example_text))

                    date_str = example['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    trans_id = str(example['transaction_id'])
                    price_fmt = f"{int(example['price']):,}".replace(",", " ") + " тг"
                    err_short = _error_short(example['error_texts'][0]) if example.get('error_texts') else "—"
                    club_lines.append(f"- {date_str} | {trans_id} | {price_fmt} | {err_short}")
                allure_error_blocks.append("\n".join(club_lines))
                if error_count >= 25:
                    break
        if error_count == 0:
            print("\nНет транзакций с ошибочными чеками")
            allure_error_blocks.append("Нет транзакций с ошибочными чеками")
        if allure_error_blocks:
            allure.attach(
                "\n\n".join(allure_error_blocks),
                name="Примеры ошибочных транзакций",
                attachment_type=allure.attachment_type.TEXT
            )

        # Сводная таблица ошибок по клубам
        summary_rows = []
        for club_id, stats in sorted_clubs_by_problems:
            if stats["with_error_receipts"] > 0 and stats["error_examples"]:
                first = stats["error_examples"][0]
                summary_rows.append({
                    "club": stats["name"],
                    "error_count": stats["with_error_receipts"],
                    "error_text": first["error_texts"][0] if first.get("error_texts") else "—",
                    "last_transaction_id": str(first["transaction_id"]),
                    "last_transaction_date": first["created_at"].strftime("%Y-%m-%d %H:%M"),
                })
        if summary_rows:
            allure.attach(
                _clubs_errors_summary_to_html(summary_rows),
                name="Сводка ошибок по клубам",
                attachment_type=allure.attachment_type.HTML
            )
        if error_type_stats:
            error_type_rows = sorted(
                [{"error_text": k, **v} for k, v in error_type_stats.items()],
                key=lambda x: -x["count"]
            )
            allure.attach(
                _error_types_to_html(error_type_rows),
                name="Ошибки по типам",
                attachment_type=allure.attachment_type.HTML
            )

        # Примеры транзакций без чеков
        print("\n" + "=" * 110)
        print("ПРИМЕРЫ ТРАНЗАКЦИЙ БЕЗ ЧЕКОВ (до 5 на клуб)")
        print("=" * 110)
        empty_count = 0
        allure_empty_blocks = []
        for club_id, stats in sorted_clubs_by_problems:
            if stats["empty_examples"]:
                club_info = f"\nКлуб: {stats['name']}\nВсего без чеков: {stats['without_receipts']}\n"
                print(club_info)
                club_lines = [f"Клуб: {stats['name']} ({stats['without_receipts']})"]
                for example in stats["empty_examples"]:
                    empty_count += 1
                    date_str = example['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    trans_id = str(example['transaction_id'])
                    price_fmt = f"{int(example['price']):,}".replace(",", " ") + " тг"
                    product_type = example.get('productType') or '—'
                    example_text = [
                        f"  - Transaction: {example['transaction_id']}",
                        f"    Сумма: {example['price']} тг",
                        f"    Тип продукта: {example.get('productType', 'N/A')}",
                        f"    Дата: {date_str}"
                    ]
                    print("\n".join(example_text))
                    club_lines.append(f"- {date_str} | {trans_id} | {price_fmt} | {product_type}")
                allure_empty_blocks.append("\n".join(club_lines))
                if empty_count >= 25:
                    break
        if empty_count == 0:
            print("\nВсе транзакции имеют чеки")
            allure_empty_blocks.append("Все транзакции имеют чеки")
        allure.attach(
            "\n\n".join(allure_empty_blocks),
            name="Примеры транзакций без чеков",
            attachment_type=allure.attachment_type.TEXT
        )

    # ── Шаг 3: Итоговая оценка ────────────────────────────────────────────
    with allure.step("Итоговая оценка"):
        print("\n" + "=" * 110)
        print("ИТОГОВАЯ ОЦЕНКА")
        print("=" * 110)

        warnings = []
        if total_transactions > 0:
            print(f"\nУспешных транзакций с чеками: {total_success} ({success_rate:.1f}%)")
            print(f"Транзакций с ошибочными чеками: {total_errors} ({error_rate:.1f}%)")
            print(f"Транзакций без чеков: {total_empty} ({empty_rate:.1f}%)")

            if total_errors > 0:
                warnings.append(f"Есть транзакции с ошибочными чеками: {total_errors} ({error_rate:.1f}%)")
            if empty_rate > 90:
                warnings.append(f"Большинство транзакций без чеков: {empty_rate:.1f}% (порог: 90%)")
            if success_rate > 20:
                print(f"\nХороший показатель успешных чеков: {success_rate:.1f}%")

        print("\n" + "=" * 110)

        if warnings:
            warnings_text = "\n".join(warnings)
            allure.attach(
                warnings_text,
                name="❌ Нарушения порогов",
                attachment_type=allure.attachment_type.TEXT
            )

            clubs_with_errors = [
                (stats, stats["with_error_receipts"])
                for _, stats in sorted_clubs_by_problems
                if stats["with_error_receipts"] > 0
            ]

            def _classify_severity(stats: dict) -> str:
                main_error = ""
                if stats["error_text_counts"]:
                    main_error = max(stats["error_text_counts"], key=stats["error_text_counts"].get).lower()
                if "автономном режиме" in main_error or "офд" in main_error or "72" in main_error:
                    return "critical"
                if "лицензи" in main_error:
                    return "critical"
                return "medium"

            def _main_error_short(stats: dict) -> str:
                if not stats["error_text_counts"]:
                    return "неизвестная ошибка"
                main_error = max(stats["error_text_counts"], key=stats["error_text_counts"].get)
                et = main_error.lower()
                if "автономном режиме" in et or "72" in et:
                    return "ОФД offline > 72h"
                if "лицензи" in et:
                    return "нет лицензии"
                if "сумма" in et and ("меньше" in et or "не может" in et):
                    return "сумма < 0"
                if "безналичной" in et and "больше" in et:
                    return "безнал > итого"
                if "отменена" in et:
                    return "транзакция отменена"
                return main_error[:60]

            critical_clubs = [(s, cnt) for s, cnt in clubs_with_errors if _classify_severity(s) == "critical"]
            medium_clubs = [(s, cnt) for s, cnt in clubs_with_errors if _classify_severity(s) == "medium"]

            summary_lines = [
                "❌ WebKassa monitoring FAILED",
                "",
                f"Всего транзакций: {total_transactions}",
                f"Ошибочных: {total_errors} ({error_rate:.1f}%)",
                f"Затронуто клубов: {len(clubs_with_errors)}",
            ]
            if critical_clubs:
                summary_lines.append("")
                summary_lines.append("🔴 Critical:")
                for s, cnt in critical_clubs:
                    summary_lines.append(f"  - {_short_club_name(s['name'])} — {cnt} ошибок ({_main_error_short(s)})")
            if medium_clubs:
                summary_lines.append("")
                summary_lines.append("🟠 Medium:")
                for s, cnt in medium_clubs:
                    summary_lines.append(f"  - {_short_club_name(s['name'])} — {cnt} ({_main_error_short(s)})")

            assert not warnings, "\n".join(summary_lines)


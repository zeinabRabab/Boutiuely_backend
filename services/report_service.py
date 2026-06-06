"""
Report Generation Service
==========================
Generates downloadable PDF and CSV reports from live database data.
PDF uses ReportLab with a modern enterprise design.
CSV uses stdlib csv for zero-dependency exports.
"""
import io
import csv
from datetime import datetime
from typing import Tuple
from sqlalchemy.orm import Session

from services.analytics_service import (
    get_dashboard_stats,
    get_top_products,
    get_revenue_trend,
    generate_full_analysis,
    get_order_status_breakdown,
    get_category_breakdown,
    get_inventory_summary,
)


def generate_csv_report(db: Session) -> Tuple[bytes, str]:
    stats = get_dashboard_stats(db)
    top_products = get_top_products(db)
    revenue_trend = get_revenue_trend(db)
    analysis = generate_full_analysis(db)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["BOUTIQUELY AI — BUSINESS REPORT"])
    writer.writerow([f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"])
    writer.writerow([])
    writer.writerow(["── OVERVIEW ──"])
    writer.writerow(["Metric", "Value"])
    for label, val in [
        ("Total Revenue", f"${stats.total_revenue:,.2f}"),
        ("Total Orders", stats.total_orders),
        ("Total Users", stats.total_users),
        ("Total Products", stats.total_products),
        ("Pending Orders", stats.pending_orders),
        ("Delivered Orders", stats.delivered_orders),
        ("Low Stock Items", stats.low_stock_count),
        ("Avg Order Value", f"${stats.total_revenue/max(stats.total_orders,1):,.2f}"),
    ]:
        writer.writerow([label, val])
    writer.writerow([])

    writer.writerow(["── TOP SELLING PRODUCTS ──"])
    writer.writerow(["Rank", "Product", "Category", "Units Sold", "Revenue"])
    for i, p in enumerate(top_products, 1):
        writer.writerow([i, p.name, p.category or "N/A", p.total_sold, f"${p.total_revenue:.2f}"])
    writer.writerow([])

    writer.writerow(["── REVENUE TREND ──"])
    writer.writerow(["Date", "Revenue", "Orders"])
    for r in revenue_trend:
        writer.writerow([r.date, f"${r.revenue:.2f}", r.orders])
    writer.writerow([])

    writer.writerow(["── AI INSIGHTS ──"])
    for insight in analysis.insights:
        writer.writerow([insight])
    writer.writerow([])

    writer.writerow(["── RECOMMENDATIONS ──"])
    for rec in analysis.recommendations:
        writer.writerow([rec])

    filename = f"boutiquely_report_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv"
    return output.getvalue().encode("utf-8"), filename


def generate_pdf_report(db: Session) -> Tuple[bytes, str]:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import HexColor, white, black
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, KeepTogether, PageBreak,
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        raise ImportError("reportlab is required: pip install reportlab")

    stats = get_dashboard_stats(db)
    top_products = get_top_products(db, limit=10)
    revenue_trend = get_revenue_trend(db, days=30)
    analysis = generate_full_analysis(db)
    order_status = get_order_status_breakdown(db)
    category_data = get_category_breakdown(db)
    inventory = get_inventory_summary(db)

    now = datetime.utcnow()
    buffer = io.BytesIO()

    # ── Colors ────────────────────────────────────────────────────────────────
    PURPLE      = HexColor("#7c3aed")
    PURPLE_DARK = HexColor("#5b21b6")
    PURPLE_LIGHT= HexColor("#f5f3ff")
    PURPLE_MID  = HexColor("#ede9fe")
    ACCENT_PINK = HexColor("#ec4899")
    DARK_TEXT   = HexColor("#1e1b4b")
    MID_TEXT    = HexColor("#4b5563")
    LIGHT_BG    = HexColor("#fafafa")
    SUCCESS     = HexColor("#059669")
    WARNING     = HexColor("#d97706")
    DANGER      = HexColor("#dc2626")
    BORDER      = HexColor("#e5e7eb")

    PAGE_W = A4[0]
    M = 1.8 * cm  # margin

    def make_doc():
        return SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=M, leftMargin=M,
            topMargin=M, bottomMargin=M + 0.8*cm,
        )

    doc = make_doc()
    styles = getSampleStyleSheet()

    def style(name, **kw):
        return ParagraphStyle(name, **kw)

    title_s   = style("T", fontSize=28, textColor=white, alignment=TA_CENTER, fontName="Helvetica-Bold", leading=34)
    sub_s     = style("S", fontSize=11, textColor=HexColor("#ddd6fe"), alignment=TA_CENTER, fontName="Helvetica")
    sec_s     = style("Sec", fontSize=13, textColor=PURPLE_DARK, fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=6)
    body_s    = style("B", fontSize=9.5, textColor=DARK_TEXT, fontName="Helvetica", leading=14)
    small_s   = style("Sm", fontSize=8.5, textColor=MID_TEXT, fontName="Helvetica", leading=12)
    bullet_s  = style("Bul", fontSize=9.5, textColor=DARK_TEXT, fontName="Helvetica", leftIndent=14, spaceAfter=3, leading=14)
    footer_s  = style("Ft", fontSize=8, textColor=MID_TEXT, alignment=TA_CENTER, fontName="Helvetica-Oblique")
    label_s   = style("Lbl", fontSize=8, textColor=MID_TEXT, fontName="Helvetica", alignment=TA_CENTER)
    kpi_s     = style("KPI", fontSize=18, textColor=PURPLE_DARK, fontName="Helvetica-Bold", alignment=TA_CENTER)
    kpi_sub_s = style("KSub", fontSize=8.5, textColor=MID_TEXT, fontName="Helvetica", alignment=TA_CENTER)

    COL = PAGE_W - 2 * M  # usable width

    def tbl_style_base(header_bg=PURPLE):
        return TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), header_bg),
            ("TEXTCOLOR",     (0,0), (-1,0), white),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0), 9),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [white, PURPLE_LIGHT]),
            ("GRID",          (0,0), (-1,-1), 0.3, BORDER),
            ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
            ("FONTSIZE",      (0,1), (-1,-1), 8.5),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("RIGHTPADDING",  (0,0), (-1,-1), 8),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ])

    def section_header(title: str):
        return [
            Spacer(1, 0.3*cm),
            HRFlowable(width="100%", color=PURPLE_MID, thickness=1.5),
            Spacer(1, 0.1*cm),
            Paragraph(title, sec_s),
        ]

    story = []

    # ──────────────────────────────────────────────────────────────────────────
    # COVER PAGE
    # ──────────────────────────────────────────────────────────────────────────
    cover = Table([[Paragraph("🛍️  BOUTIQUELY AI", title_s)]], colWidths=[COL])
    cover.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), PURPLE),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 28),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("ROUNDEDCORNERS",[10]),
    ]))
    story.append(cover)

    sub_tbl = Table([[Paragraph("Business Analytics Report", sub_s)]], colWidths=[COL])
    sub_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), PURPLE),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 28),
    ]))
    story.append(sub_tbl)

    meta_tbl = Table([
        [Paragraph(f"<b>Report Date:</b>  {now.strftime('%B %d, %Y')}", body_s),
         Paragraph(f"<b>Generated:</b>  {now.strftime('%H:%M UTC')}", body_s),
         Paragraph(f"<b>Confidential</b>", body_s)],
    ], colWidths=[COL/3]*3)
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0),(-1,-1), PURPLE_LIGHT),
        ("TOPPADDING",  (0,0),(-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("LEFTPADDING", (0,0),(-1,-1), 10),
        ("GRID",        (0,0),(-1,-1), 0.3, BORDER),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 0.5*cm))

    # ──────────────────────────────────────────────────────────────────────────
    # EXECUTIVE SUMMARY
    # ──────────────────────────────────────────────────────────────────────────
    story += section_header("1.  Executive Summary")
    story.append(Paragraph(
        f"This report covers the Boutiquely AI e-commerce platform as of <b>{now.strftime('%B %d, %Y')}</b>. "
        f"The store has processed <b>{stats.total_orders:,}</b> orders totalling "
        f"<b>${stats.total_revenue:,.2f}</b> in revenue across <b>{stats.total_products}</b> products "
        f"and <b>{stats.total_users}</b> registered users. "
        f"<b>{stats.low_stock_count}</b> product(s) are flagged for restocking.",
        body_s,
    ))
    story.append(Spacer(1, 0.3*cm))

    # ──────────────────────────────────────────────────────────────────────────
    # KPI CARDS (2×4 grid)
    # ──────────────────────────────────────────────────────────────────────────
    story += section_header("2.  Key Performance Indicators")

    kpi_items = [
        ("💰 Revenue",          f"${stats.total_revenue:,.2f}",  PURPLE_LIGHT),
        ("📦 Orders",           f"{stats.total_orders:,}",       PURPLE_LIGHT),
        ("👥 Users",            f"{stats.total_users:,}",        PURPLE_LIGHT),
        ("🏷️ Products",         f"{stats.total_products:,}",     PURPLE_LIGHT),
        ("⏳ Pending",          f"{stats.pending_orders:,}",     HexColor("#fffbeb")),
        ("✅ Delivered",        f"{stats.delivered_orders:,}",   HexColor("#f0fdf4")),
        ("⚠️ Low Stock",        f"{stats.low_stock_count:,}",    HexColor("#fff1f2")),
        ("📊 Avg Order",        f"${stats.total_revenue/max(stats.total_orders,1):,.2f}", PURPLE_LIGHT),
    ]

    # 4-across grid
    kpi_data = [[
        Table([[Paragraph(label, label_s)], [Paragraph(val, kpi_s)]], colWidths=[(COL/4)-0.2*cm])
        for label, val, bg in kpi_items[:4]
    ], [
        Table([[Paragraph(label, label_s)], [Paragraph(val, kpi_s)]], colWidths=[(COL/4)-0.2*cm])
        for label, val, bg in kpi_items[4:]
    ]]

    kpi_tbl = Table(kpi_data, colWidths=[(COL/4)]*4, rowHeights=[2.0*cm, 2.0*cm])
    kpi_styles = []
    for row_i, row in enumerate(kpi_items):
        label, val, bg = row
        col_i = row_i % 4
        row_j = row_i // 4
        kpi_styles += [
            ("BACKGROUND",    (col_i, row_j), (col_i, row_j), bg),
            ("TOPPADDING",    (col_i, row_j), (col_i, row_j), 6),
            ("BOTTOMPADDING", (col_i, row_j), (col_i, row_j), 6),
        ]
    kpi_tbl.setStyle(TableStyle([
        ("GRID",     (0,0),(-1,-1), 0.5, BORDER),
        ("VALIGN",   (0,0),(-1,-1), "MIDDLE"),
        ("ALIGN",    (0,0),(-1,-1), "CENTER"),
    ] + kpi_styles))
    story.append(kpi_tbl)

    # ──────────────────────────────────────────────────────────────────────────
    # TOP PRODUCTS
    # ──────────────────────────────────────────────────────────────────────────
    if top_products:
        story += section_header("3.  Product Performance")
        prod_data = [["#", "Product Name", "Category", "Units Sold", "Revenue", "% of Total"]]
        total_rev = sum(p.total_revenue for p in top_products)
        for i, p in enumerate(top_products[:10], 1):
            pct = (p.total_revenue / max(total_rev, 0.01)) * 100
            prod_data.append([
                str(i), p.name[:32], p.category or "N/A",
                f"{p.total_sold:,}", f"${p.total_revenue:,.2f}", f"{pct:.1f}%"
            ])
        prod_tbl = Table(prod_data, colWidths=[0.6*cm, 5.8*cm, 3.2*cm, 2.3*cm, 2.8*cm, 2.3*cm])
        prod_tbl.setStyle(tbl_style_base())
        prod_tbl.setStyle(TableStyle([
            ("ALIGN",  (3,0), (5,-1), "RIGHT"),
        ] + tbl_style_base()._cmds))
        story.append(prod_tbl)

    # ──────────────────────────────────────────────────────────────────────────
    # REVENUE TREND
    # ──────────────────────────────────────────────────────────────────────────
    story += section_header("4.  Revenue Trend — Last 30 Days")

    # Show a mini sparkline via ASCII bar chart substitute (table with width bars)
    # Group by week for compactness
    rev_data = [["Date", "Revenue ($)", "Orders", "Daily Avg"]]
    for r in revenue_trend[-14:]:  # last 14 in PDF
        rev_data.append([
            r.date, f"${r.revenue:,.2f}", str(r.orders),
            f"${r.revenue/max(r.orders,1):,.2f}",
        ])

    rev_tbl = Table(rev_data, colWidths=[3.5*cm, 4*cm, 3*cm, 3.5*cm])
    rev_tbl.setStyle(tbl_style_base())
    story.append(rev_tbl)

    # Totals row
    total_period = sum(r.revenue for r in revenue_trend)
    total_orders = sum(r.orders for r in revenue_trend)
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph(
        f"<b>30-day total:</b> ${total_period:,.2f} revenue · {total_orders:,} orders · "
        f"avg ${total_period/max(total_orders,1):,.2f}/order",
        small_s,
    ))

    # ──────────────────────────────────────────────────────────────────────────
    # ORDER STATUS
    # ──────────────────────────────────────────────────────────────────────────
    story += section_header("5.  Orders Analysis")
    status_data = [["Status", "Count", "% of Total"]]
    total_orders_count = sum(r.count for r in order_status)
    for r in order_status:
        pct = (r.count / max(total_orders_count, 1)) * 100
        status_data.append([r.status.capitalize(), str(r.count), f"{pct:.1f}%"])
    status_data.append(["TOTAL", str(total_orders_count), "100%"])

    stat_tbl = Table(status_data, colWidths=[5*cm, 3*cm, 3*cm])
    s = tbl_style_base()
    s.add("BACKGROUND", (0,-1), (-1,-1), PURPLE_MID)
    s.add("FONTNAME",   (0,-1), (-1,-1), "Helvetica-Bold")
    stat_tbl.setStyle(s)
    story.append(stat_tbl)

    # ──────────────────────────────────────────────────────────────────────────
    # CATEGORY BREAKDOWN
    # ──────────────────────────────────────────────────────────────────────────
    if category_data:
        story += section_header("6.  Revenue by Category")
        cat_data = [["Category", "Orders", "Units Sold", "Revenue"]]
        for c in category_data:
            cat_data.append([
                c["category"], str(c["order_count"]), str(c["units_sold"]),
                f"${c['revenue']:,.2f}",
            ])
        cat_tbl = Table(cat_data, colWidths=[5*cm, 3*cm, 3*cm, 3.5*cm])
        cat_tbl.setStyle(tbl_style_base())
        story.append(cat_tbl)

    # ──────────────────────────────────────────────────────────────────────────
    # INVENTORY STATUS
    # ──────────────────────────────────────────────────────────────────────────
    story += section_header("7.  Inventory Status")
    inv_summary = [
        ["Total Products", str(inventory["total_products"])],
        ["Total Stock Value", f"${inventory['total_stock_value']:,.2f}"],
        ["Out of Stock", str(inventory["out_of_stock"])],
        ["Low Stock (≤ threshold)", str(inventory["low_stock"])],
        ["Healthy Stock", str(inventory["healthy_stock"])],
    ]
    inv_tbl = Table(inv_summary, colWidths=[7*cm, 7*cm])
    inv_tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [white, PURPLE_LIGHT]),
        ("GRID",     (0,0), (-1,-1), 0.3, BORDER),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
    ]))
    story.append(inv_tbl)

    # ──────────────────────────────────────────────────────────────────────────
    # AI INSIGHTS & RECOMMENDATIONS
    # ──────────────────────────────────────────────────────────────────────────
    story += section_header("8.  AI Insights")
    for insight in analysis.insights:
        story.append(Paragraph(f"• &nbsp; {insight}", bullet_s))
    story.append(Spacer(1, 0.2*cm))

    story += section_header("9.  Recommendations")
    for i, rec in enumerate(analysis.recommendations, 1):
        story.append(Paragraph(f"{i}.  {rec}", bullet_s))

    # ──────────────────────────────────────────────────────────────────────────
    # FOOTER
    # ──────────────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.6*cm))
    story.append(HRFlowable(width="100%", color=PURPLE, thickness=1.5))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph(
        f"Generated by <b>Boutiquely AI Platform</b>  ·  {now.strftime('%B %d, %Y %H:%M UTC')}  ·  Confidential & Proprietary",
        footer_s,
    ))

    doc.build(story)
    buffer.seek(0)
    filename = f"boutiquely_report_{now.strftime('%Y%m%d_%H%M')}.pdf"
    return buffer.read(), filename

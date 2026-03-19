from typing import Iterable

from app.models.patient import Patient
from app.schemas.report import ReportPreviewResponse, ReportPreviewSection
from app.services.patient_service import build_patient_detail_query
from app.services.recommendation_config_service import load_recommendation_config
from app.services.recommendation_service import evaluate_patient


def _lines(*items: str) -> list[str]:
    return [item for item in items if item and item != "未填写"]


def build_report_preview(db, patient_id: int, *, auto_generate: bool = False) -> ReportPreviewResponse:
    patient = db.scalar(build_patient_detail_query().where(Patient.id == patient_id))
    if patient is None:
        raise ValueError("患者不存在")

    config = load_recommendation_config()
    prediction = patient.prediction_result
    if prediction is None and auto_generate:
        evaluate_patient(db, patient_id, save_result=True)
        patient = db.scalar(build_patient_detail_query().where(Patient.id == patient_id))
        prediction = patient.prediction_result

    if prediction is None:
        raise ValueError("当前患者尚未生成推荐结果，请先在评估/推荐中心执行评估")

    sections = [
        ReportPreviewSection(
            title="基本信息",
            content=_lines(
                f"患者编号：{patient.patient_code}",
                f"匿名编号：{patient.anonymized_code}",
                f"性别：{patient.gender or '未填写'}",
                f"年龄：{patient.age if patient.age is not None else '未填写'}",
                f"教育程度：{patient.education_level or '未填写'}",
            ),
        ),
        ReportPreviewSection(
            title="数据完整性",
            content=_lines(
                f"数据完整性评分：{prediction.data_completeness_score if prediction.data_completeness_score is not None else '未填写'}",
                prediction.explanation_text or "",
            ),
        ),
        ReportPreviewSection(
            title="推荐等级",
            content=_lines(
                f"推荐等级：{prediction.recommendation_level or '未填写'}",
                f"获益评分：{prediction.benefit_score if prediction.benefit_score is not None else '未填写'}",
            ),
        ),
        ReportPreviewSection(
            title="关键因素",
            content=list(prediction.key_factors) or ["当前未提取到关键影响因素"],
        ),
        ReportPreviewSection(
            title="限制说明",
            content=list(prediction.usage_limitations) or list(config.limitation_templates),
        ),
    ]

    return ReportPreviewResponse(
        patient_id=patient.id,
        patient_code=patient.patient_code,
        anonymized_code=patient.anonymized_code,
        generated_at=prediction.generated_at,
        data_completeness_score=prediction.data_completeness_score,
        benefit_score=prediction.benefit_score,
        recommendation_level=prediction.recommendation_level,
        explanation_text=prediction.explanation_text,
        key_factors=prediction.key_factors,
        usage_limitations=prediction.usage_limitations,
        footer_notice=config.report_footer_notice,
        sections=sections,
    )


def render_report_html(report: ReportPreviewResponse) -> str:
    section_html = []
    for section in report.sections:
        items_html = "".join(f"<li>{item}</li>" for item in section.content)
        section_html.append(
            f"""
            <section class="report-section">
              <h2>{section.title}</h2>
              <ul>{items_html}</ul>
            </section>
            """
        )

    return f"""
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <title>科研辅助推荐报告 - {report.patient_code}</title>
    <style>
      body {{
        font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
        margin: 0;
        background: #f4f6f9;
        color: #173654;
      }}
      .page {{
        width: 900px;
        margin: 24px auto;
        background: #fff;
        padding: 36px 42px;
        box-sizing: border-box;
      }}
      h1 {{
        margin: 0 0 8px;
        font-size: 28px;
      }}
      .meta {{
        color: #63788e;
        line-height: 1.8;
        margin-bottom: 24px;
      }}
      .highlight {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-bottom: 24px;
      }}
      .highlight-card {{
        border: 1px solid #d8e4ef;
        border-radius: 12px;
        padding: 16px;
        background: #f9fcff;
      }}
      .highlight-card span {{
        color: #6c7f92;
        font-size: 13px;
      }}
      .highlight-card strong {{
        display: block;
        margin-top: 10px;
        font-size: 28px;
      }}
      .report-section {{
        margin-bottom: 24px;
        page-break-inside: avoid;
      }}
      .report-section h2 {{
        margin: 0 0 12px;
        font-size: 20px;
      }}
      .report-section ul {{
        margin: 0;
        padding-left: 20px;
        line-height: 1.9;
      }}
      .notice {{
        margin-top: 28px;
        padding: 16px;
        border-radius: 10px;
        background: #fff7e8;
        color: #8a5b00;
        font-weight: 600;
      }}
      @media print {{
        body {{
          background: #fff;
        }}
        .page {{
          width: auto;
          margin: 0;
          padding: 12mm;
        }}
      }}
    </style>
  </head>
  <body>
    <div class="page">
      <h1>慢性失眠光干预科研辅助推荐报告</h1>
      <div class="meta">
        患者编号：{report.patient_code}<br />
        匿名编号：{report.anonymized_code}<br />
        生成时间：{report.generated_at or "未生成"}
      </div>
      <div class="highlight">
        <div class="highlight-card">
          <span>数据完整性</span>
          <strong>{report.data_completeness_score or "未填写"}</strong>
        </div>
        <div class="highlight-card">
          <span>获益评分</span>
          <strong>{report.benefit_score or "未填写"}</strong>
        </div>
        <div class="highlight-card">
          <span>推荐等级</span>
          <strong>{report.recommendation_level or "未填写"}</strong>
        </div>
      </div>
      {''.join(section_html)}
      <div class="notice">{report.footer_notice}</div>
    </div>
  </body>
</html>
    """.strip()


def render_export_csv(rows: Iterable[ReportPreviewResponse]) -> bytes:
    lines = ["患者编号,匿名编号,推荐等级,数据完整性,获益评分,生成时间"]
    for row in rows:
        lines.append(
            f"{row.patient_code},{row.anonymized_code},{row.recommendation_level or ''},"
            f"{row.data_completeness_score or ''},{row.benefit_score or ''},{row.generated_at or ''}"
        )
    return "\n".join(lines).encode("utf-8-sig")

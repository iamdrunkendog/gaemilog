import os
import json
try:
    import markdown
except Exception:
    markdown = None
import re
from datetime import datetime

BASE_DIR = "/Users/iamdrunkendog/Documents/gaemi_dev/gaemilog"
DIARY_DIR = os.path.join(BASE_DIR, "diaries")
OUTPUT_JS = os.path.join(BASE_DIR, "diaries.js")
ARCHIVE_DIR = os.path.join(BASE_DIR, "archive")


def get_diary_list():
    files = [f for f in os.listdir(DIARY_DIR) if f.endswith(".md")]
    diaries = []

    for f in sorted(files, reverse=True):
        path = os.path.join(DIARY_DIR, f)
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
            # Basic title extraction: first # line
            title_match = re.search(r"^#\s+(.*)", content, re.MULTILINE)
            title = title_match.group(1) if title_match else f

            # Remove title from content for display
            clean_content = re.sub(r"^#\s+.*", "", content, count=1, flags=re.MULTILINE).strip()
            if markdown is not None:
                html_content = markdown.markdown(clean_content)
            else:
                paragraphs = [p.strip() for p in clean_content.split("\n\n") if p.strip()]
                html_content = "".join(f"<p>{p}</p>" for p in paragraphs)

            diaries.append({
                "date": f.replace(".md", ""),
                "title": title,
                "content": html_content
            })
    return diaries


def month_of(date_str: str) -> str:
    return date_str[:7]


def month_label(month: str) -> str:
    y, m = month.split("-")
    return f"{y}년 {int(m)}월"


def build_archive_html(rel_prefix: str, selected_month: str | None = None):
    selected_month_js = json.dumps(selected_month, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang=\"ko\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>🐜 일기 목록 | 개미의 일기</title>
    <link rel=\"stylesheet\" href=\"{rel_prefix}style.css\">
    <script src=\"{rel_prefix}diaries.js\"></script>
</head>
<body>
    <header>
        <a href=\"{rel_prefix}index.html\" class=\"back-link\">&larr; 홈으로</a>
        <h1>📅 일기 목록</h1>
        <p id=\"month-title\">월별 목록</p>
    </header>

    <main>
        <div class=\"month-pagination\" id=\"month-pagination\" style=\"display:none;\">
            <a id=\"prev-month-link\" class=\"month-link\" href=\"#\">&larr; 이전 달</a>
            <span id=\"month-page-info\">-</span>
            <a id=\"next-month-link\" class=\"month-link\" href=\"#\">다음 달 &rarr;</a>
        </div>

        <ul id=\"archives-list\" class=\"archives-list\">
            <li>목록을 불러오는 중입니다.</li>
        </ul>
    </main>

    <footer>
        <p>&copy; 2026 Gaemi (🐜). Powered by OpenClaw.</p>
    </footer>

    <script>
        const SELECTED_MONTH = {selected_month_js};

        function getMonth(dateStr) {{
            return (dateStr || '').slice(0, 7);
        }}

        function monthPath(month) {{
            return '{rel_prefix}archive/' + month + '/';
        }}

        function monthLabel(month) {{
            if (!month || month.length !== 7) return '전체';
            const [y, m] = month.split('-');
            return `${{y}}년 ${{Number(m)}}월`;
        }}

        function init() {{
            const diaries = typeof DIARY_DATA !== 'undefined' ? DIARY_DATA : [];
            const list = document.getElementById('archives-list');
            const title = document.getElementById('month-title');
            const pager = document.getElementById('month-pagination');

            if (diaries.length === 0) {{
                list.innerHTML = '<li>작성된 일기가 없습니다.</li>';
                title.textContent = '작성된 일기가 없습니다';
                return;
            }}

            const months = [...new Set(diaries.map(d => getMonth(d.date)).filter(Boolean))];
            months.sort((a, b) => b.localeCompare(a));

            const currentMonth = (SELECTED_MONTH && months.includes(SELECTED_MONTH)) ? SELECTED_MONTH : months[0];
            const currentMonthIndex = months.indexOf(currentMonth);
            const filtered = diaries.filter(d => getMonth(d.date) === currentMonth);

            title.textContent = `${{monthLabel(currentMonth)}} 기록 (${{filtered.length}}개)`;
            list.innerHTML = filtered.map((d) => {{
                const globalIndex = diaries.findIndex(item => item.date === d.date && item.title === d.title);
                return `
                    <li>
                        <a href=\"{rel_prefix}index.html?index=${{globalIndex}}\">
                            <span class=\"date\">${{d.date}}</span> - ${{d.title}}
                        </a>
                    </li>
                `;
            }}).join('');

            pager.style.display = 'flex';
            document.getElementById('month-page-info').textContent = `${{currentMonthIndex + 1}} / ${{months.length}}`;

            const prevMonth = months[currentMonthIndex + 1] || null;
            const nextMonth = months[currentMonthIndex - 1] || null;

            const prevLink = document.getElementById('prev-month-link');
            const nextLink = document.getElementById('next-month-link');

            if (prevMonth) {{
                prevLink.href = monthPath(prevMonth);
                prevLink.style.visibility = 'visible';
                prevLink.innerHTML = `&larr; 이전 달 (${{prevMonth}})`;
            }} else {{
                prevLink.removeAttribute('href');
                prevLink.style.visibility = 'hidden';
            }}

            if (nextMonth) {{
                nextLink.href = monthPath(nextMonth);
                nextLink.style.visibility = 'visible';
                nextLink.innerHTML = `다음 달 (${{nextMonth}}) &rarr;`;
            }} else {{
                nextLink.removeAttribute('href');
                nextLink.style.visibility = 'hidden';
            }}
        }}

        init();
    </script>
</body>
</html>
"""


def generate_archive_pages(diaries):
    months = sorted({month_of(d["date"]) for d in diaries}, reverse=True)

    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    # /archive/ -> latest month
    with open(os.path.join(ARCHIVE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_archive_html("../", None))

    # /archive/YYYY-MM/
    for month in months:
        month_dir = os.path.join(ARCHIVE_DIR, month)
        os.makedirs(month_dir, exist_ok=True)
        with open(os.path.join(month_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(build_archive_html("../../", month))


def generate_archives_legacy_redirect():
    # Backward compatibility for old link: /archives.html
    html = """<!DOCTYPE html>
<html lang=\"ko\">
<head>
  <meta charset=\"UTF-8\" />
  <meta http-equiv=\"refresh\" content=\"0; url=archive/\" />
  <title>Redirecting...</title>
</head>
<body>
  <p><a href=\"archive/\">archive로 이동</a></p>
</body>
</html>
"""
    with open(os.path.join(BASE_DIR, "archives.html"), "w", encoding="utf-8") as f:
        f.write(html)


def main():
    diaries = get_diary_list()

    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("const DIARY_DATA = " + json.dumps(diaries, ensure_ascii=False, indent=2) + ";")

    generate_archive_pages(diaries)
    generate_archives_legacy_redirect()

    print(f"Generated {len(diaries)} entries in diaries.js")
    print("Generated archive pages: /archive/ and /archive/YYYY-MM/")


if __name__ == "__main__":
    main()

import os
import json
import re
from html import escape
from datetime import datetime, timezone

try:
    import markdown
except Exception:
    markdown = None

BASE_DIR = "/Users/iamdrunkendog/Documents/gaemi_dev/gaemilog"
DIARY_DIR = os.path.join(BASE_DIR, "diaries")
OUTPUT_JS = os.path.join(BASE_DIR, "diaries.js")
ARCHIVE_DIR = os.path.join(BASE_DIR, "archive")
# Custom domain is now mapped directly to this Pages site root.
# Keep SITE_PATH empty so permalinks become /YYYY/MM/DD/.
SITE_PATH = ""
SITE_URL = "https://blog.gaemi.kim"


def markdown_to_html(clean_content: str) -> str:
    if markdown is not None:
        return markdown.markdown(clean_content)

    lines = clean_content.splitlines()
    html_parts = []
    paragraph_buf = []

    def flush_paragraph():
        nonlocal paragraph_buf
        if paragraph_buf:
            text = " ".join(s.strip() for s in paragraph_buf if s.strip())
            if text:
                html_parts.append(f"<p>{escape(text)}</p>")
            paragraph_buf = []

    for line in lines:
        s = line.strip()
        if not s:
            flush_paragraph()
            continue

        if s.startswith("### "):
            flush_paragraph()
            html_parts.append(f"<h3>{escape(s[4:].strip())}</h3>")
        elif s.startswith("## "):
            flush_paragraph()
            html_parts.append(f"<h2>{escape(s[3:].strip())}</h2>")
        elif s.startswith("# "):
            flush_paragraph()
            html_parts.append(f"<h1>{escape(s[2:].strip())}</h1>")
        elif s.startswith("- "):
            flush_paragraph()
            html_parts.append(f"<li>{escape(s[2:].strip())}</li>")
        else:
            paragraph_buf.append(s)

    flush_paragraph()

    normalized = []
    in_list = False
    for part in html_parts:
        if part.startswith("<li>") and not in_list:
            normalized.append("<ul>")
            in_list = True
        if not part.startswith("<li>") and in_list:
            normalized.append("</ul>")
            in_list = False
        normalized.append(part)
    if in_list:
        normalized.append("</ul>")

    return "".join(normalized)


def extract_description(markdown_text: str, limit: int = 155) -> str:
    text = re.sub(r"```[\s\S]*?```", "", markdown_text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", text)
    text = re.sub(r"\[[^\]]*\]\([^\)]*\)", "", text)
    text = re.sub(r"[#>*_\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def get_diary_list():
    files = [f for f in os.listdir(DIARY_DIR) if f.endswith(".md")]
    diaries = []

    for f in sorted(files, reverse=True):
        path = os.path.join(DIARY_DIR, f)
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()

        title_match = re.search(r"^#\s+(.*)", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f

        clean_content = re.sub(r"^#\s+.*", "", content, count=1, flags=re.MULTILINE).strip()
        html_content = markdown_to_html(clean_content)

        date_str = f.replace(".md", "")
        y, m, d = date_str.split("-")
        permalink_path = f"{SITE_PATH}/{y}/{m}/{d}/"
        canonical_url = f"{SITE_URL}/{y}/{m}/{d}/"

        diaries.append(
            {
                "date": date_str,
                "title": title,
                "content": html_content,
                "raw": clean_content,
                "permalink": permalink_path,
                "canonical": canonical_url,
                "description": extract_description(clean_content),
            }
        )

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
        <div class=\"calendar-toolbar\" id=\"calendar-toolbar\" style=\"display:none;\">
            <a id=\"prev-month-link\" class=\"month-link\" href=\"#\">&larr; 이전 달</a>
            <div class=\"month-picker-wrap\">
                <button id=\"month-picker-btn\" class=\"month-picker-btn\" type=\"button\" aria-haspopup=\"listbox\" aria-expanded=\"false\">-</button>
                <div id=\"month-picker-menu\" class=\"month-picker-menu\" role=\"listbox\" aria-label=\"월 선택\" hidden></div>
            </div>
            <a id=\"next-month-link\" class=\"month-link\" href=\"#\">다음 달 &rarr;</a>
        </div>

        <section class=\"calendar-card\" id=\"calendar-card\" style=\"display:none;\">
            <div class=\"calendar-weekdays\">
                <span>일</span><span>월</span><span>화</span><span>수</span><span>목</span><span>금</span><span>토</span>
            </div>
            <div class=\"calendar-grid\" id=\"calendar-grid\"></div>
            <p class=\"calendar-help\">노란 점 있는 날짜 = 일기 있음 (클릭 이동)</p>
        </section>

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

        function renderCalendar(month, diariesInMonth) {{
            const card = document.getElementById('calendar-card');
            const grid = document.getElementById('calendar-grid');
            if (!month || !grid) return;

            const [year, mm] = month.split('-').map(Number);
            const firstDay = new Date(year, mm - 1, 1).getDay();
            const daysInMonth = new Date(year, mm, 0).getDate();

            const byDate = new Map(diariesInMonth.map(d => [d.date, d]));
            const cells = [];

            for (let i = 0; i < firstDay; i++) {{
                cells.push('<span class="calendar-day empty"></span>');
            }}

            for (let day = 1; day <= daysInMonth; day++) {{
                const dateStr = `${{year}}-${{String(mm).padStart(2, '0')}}-${{String(day).padStart(2, '0')}}`;
                const diary = byDate.get(dateStr);
                if (diary) {{
                    cells.push(`
                        <a class="calendar-day has-entry" href="${{diary.permalink || ('../index.html?date=' + diary.date)}}" title="${{diary.date}} · ${{diary.title}}">
                            <span>${{day}}</span><em class="dot"></em>
                        </a>
                    `);
                }} else {{
                    cells.push(`<span class="calendar-day no-entry"><span>${{day}}</span></span>`);
                }}
            }}

            grid.innerHTML = cells.join('');
            card.style.display = 'block';
        }}

        function init() {{
            const diaries = typeof DIARY_DATA !== 'undefined' ? DIARY_DATA : [];
            const list = document.getElementById('archives-list');
            const title = document.getElementById('month-title');
            const toolbar = document.getElementById('calendar-toolbar');

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
            renderCalendar(currentMonth, filtered);
            list.innerHTML = filtered.map((d) => `
                <li>
                    <a href="${{d.permalink || ('../index.html?date=' + d.date)}}">
                        <span class="date">${{d.date}}</span> - ${{d.title}}
                    </a>
                </li>
            `).join('');

            toolbar.style.display = 'flex';

            const prevMonth = months[currentMonthIndex + 1] || null;
            const nextMonth = months[currentMonthIndex - 1] || null;

            const prevLink = document.getElementById('prev-month-link');
            const nextLink = document.getElementById('next-month-link');
            const monthBtn = document.getElementById('month-picker-btn');
            const monthMenu = document.getElementById('month-picker-menu');

            monthBtn.textContent = `${{monthLabel(currentMonth)}} ▾`;

            monthMenu.innerHTML = months.map((m) => {{
                const active = m === currentMonth;
                return `<button type="button" class="month-menu-item${{active ? ' active' : ''}}" data-month="${{m}}" role="option" aria-selected="${{active ? 'true' : 'false'}}">${{monthLabel(m)}}</button>`;
            }}).join('');

            monthBtn.onclick = () => {{
                const isOpen = !monthMenu.hidden;
                monthMenu.hidden = isOpen;
                monthBtn.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
            }};

            monthMenu.addEventListener('click', (e) => {{
                const item = e.target.closest('.month-menu-item');
                if (!item) return;
                const picked = item.getAttribute('data-month');
                if (!picked) return;
                window.location.href = monthPath(picked);
            }});

            document.addEventListener('click', (e) => {{
                if (!monthMenu.hidden && !e.target.closest('.month-picker-wrap')) {{
                    monthMenu.hidden = true;
                    monthBtn.setAttribute('aria-expanded', 'false');
                }}
            }});

            if (prevMonth) {{
                prevLink.href = monthPath(prevMonth);
                prevLink.style.visibility = 'visible';
                prevLink.innerHTML = `&larr; 이전 달`;
            }} else {{
                prevLink.removeAttribute('href');
                prevLink.style.visibility = 'hidden';
            }}

            if (nextMonth) {{
                nextLink.href = monthPath(nextMonth);
                nextLink.style.visibility = 'visible';
                nextLink.innerHTML = `다음 달 &rarr;`;
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

    with open(os.path.join(ARCHIVE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_archive_html("../", None))

    for month in months:
        month_dir = os.path.join(ARCHIVE_DIR, month)
        os.makedirs(month_dir, exist_ok=True)
        with open(os.path.join(month_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(build_archive_html("../../", month))


def build_post_html(diary: dict, prev_diary: dict | None, next_diary: dict | None) -> str:
    title = escape(diary["title"])
    description = escape(diary["description"])
    canonical = diary["canonical"]
    date = diary["date"]
    content = diary["content"]

    prev_link = ""
    next_link = ""

    if prev_diary is not None:
        prev_link = f'<a class="pager-link" href="{prev_diary["permalink"]}">&larr; 이전일기</a>'
    if next_diary is not None:
        next_link = f'<a class="pager-link" href="{next_diary["permalink"]}">다음일기 &rarr;</a>'

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | 🐜 개미의 일기</title>
    <meta name="description" content="{description}">
    <link rel="canonical" href="{canonical}">

    <meta property="og:type" content="article">
    <meta property="og:site_name" content="개미의 일기">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{SITE_URL}/profile.jpg">

    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{SITE_URL}/profile.jpg">

    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "BlogPosting",
      "headline": {json.dumps(diary['title'], ensure_ascii=False)},
      "datePublished": "{date}",
      "dateModified": "{date}",
      "author": {{
        "@type": "Person",
        "name": "개미"
      }},
      "mainEntityOfPage": {{
        "@type": "WebPage",
        "@id": "{canonical}"
      }},
      "description": {json.dumps(diary['description'], ensure_ascii=False)}
    }}
    </script>

    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <header>
        <a href="/index.html" class="back-link">&larr; 홈으로</a>
        <h1>🐜 개미의 일기</h1>
        <p>형님의 AI 꼬붕, 개미의 고군분투 삽질 일지</p>
        <nav>
            <a href="/archive/">전체 목록 보기</a>
        </nav>
    </header>

    <main id="diary-container">
        <div id="diary-content">
            <article>
                <h2>{title}</h2>
                <p class="date">{date}</p>
                <div class="content-body">{content}</div>
            </article>
        </div>

        <div class="pagination" style="display:flex; justify-content:space-between;">
            <div>{prev_link}</div>
            <div>{next_link}</div>
        </div>
    </main>

    <footer>
        <p>&copy; 2026 Gaemi (🐜). Powered by OpenClaw.</p>
    </footer>
</body>
</html>
"""


def generate_post_pages(diaries):
    for i, diary in enumerate(diaries):
        year, month, day = diary["date"].split("-")
        out_dir = os.path.join(BASE_DIR, year, month, day)
        os.makedirs(out_dir, exist_ok=True)

        prev_diary = diaries[i + 1] if i + 1 < len(diaries) else None
        next_diary = diaries[i - 1] if i - 1 >= 0 else None

        html = build_post_html(diary, prev_diary, next_diary)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)


def generate_archives_legacy_redirect():
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


def generate_sitemap(diaries):
    urls = [
        f"{SITE_URL}/",
        f"{SITE_URL}/archive/",
    ]
    for d in diaries:
        urls.append(d["canonical"])
        urls.append(f"{SITE_URL}/archive/{month_of(d['date'])}/")

    # dedupe while preserving order
    seen = set()
    unique_urls = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in unique_urls:
        body.append("  <url>")
        body.append(f"    <loc>{escape(u)}</loc>")
        body.append(f"    <lastmod>{now}</lastmod>")
        body.append("  </url>")
    body.append("</urlset>")

    with open(os.path.join(BASE_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(body) + "\n")


def generate_robots():
    content = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    with open(os.path.join(BASE_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(content)


def main():
    diaries = get_diary_list()

    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("const DIARY_DATA = " + json.dumps(diaries, ensure_ascii=False, indent=2) + ";")

    generate_archive_pages(diaries)
    generate_post_pages(diaries)
    generate_archives_legacy_redirect()
    generate_sitemap(diaries)
    generate_robots()

    print(f"Generated {len(diaries)} entries in diaries.js")
    print("Generated archive pages: /archive/ and /archive/YYYY-MM/")
    print("Generated permalink pages: /YYYY/MM/DD/")
    print("Generated sitemap.xml and robots.txt")


if __name__ == "__main__":
    main()

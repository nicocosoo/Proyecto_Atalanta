#!/usr/bin/env python3
"""
Scrapes images from live atalantago.com articles, downloads them,
and inserts them into local HTML files at the correct positions.
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup, NavigableString

BASE_URL = "https://atalantago.com"
IMG_DIR = "imagenes"
UPLOAD_BASE = "https://atalantago.com/wp-content/uploads/"

# Map: local_html_filename -> live_url_slug
ARTICLES = {
    "noticia-declaracion-renta.html":  "que-no-estafen-declaracion-renta",
    "noticia-pinceladas-realidad.html": "ciberseguridad-pinceladas-realidad",
    "noticia-terraform.html":           "como-mantener-los-recursos-del-estado-de-terraform",
    "noticia-localstack.html":          "localstack",
    "noticia-virtualizacion-ot.html":   "virtualizacion-de-la-infraestructura-ot",
    "agile-gestion-tiempo.html":        "agile-gestion-tiempo",
    "log4shell.html":                   "log4shell",
    "spiderfoot.html":                  "spiderfoot",
    "kalitorify.html":                  "kalitorify",
    "python-library-hijacking.html":    "python-library-hijacking",
    "rce.html":                         "rce",
    "named-pipes.html":                 "named-pipes",
    "lfi.html":                         "lfi",
    "footprinting.html":                "footprinting",
    "ingenieria-social.html":           "ingenieria-social",
    "deep-web.html":                    "deep-web",
    "master-ciberseguridad-ceu.html":   "master-ciberseguridad-ceu",
    "iot-motores-de-busqueda.html":     "iot-motores-de-busqueda",
    "google-hacking.html":              "google-hacking",
    "sqlmap.html":                      "sqlmap",
    "nse-pentest.html":                 "nse-un-campo-abierto-para-el-pentest",
    "seguridad-diseno.html":            "seguridad-en-el-diseno-analisis-de-riesgos-y-cisnes-negros",
    "angular-lifecycle.html":           "angular-lifecycle-article-2",
    "hacking-con-unicode.html":         "hacking-con-unicode",
}

SKIP_ARTICLES = {"noticia-cazando-bots.html"}  # Already done

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def get_article_content(slug):
    """Fetch the live article and return the entry-content soup element."""
    url = f"{BASE_URL}/{slug}/"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # WordPress content is usually in .entry-content or .post-content
    content = (
        soup.find(class_="entry-content")
        or soup.find(class_="post-content")
        or soup.find("article")
    )
    return content

def get_article_images(content_el):
    """
    Return list of dicts: {src, filename, alt, prev_tag, prev_text}
    prev_tag/prev_text = the element that appears right before this image in the flow.
    """
    if not content_el:
        return []

    images = []
    all_imgs = content_el.find_all("img")

    for img in all_imgs:
        src = img.get("src", "")
        if not src or "wp-content/uploads" not in src:
            continue
        # Skip logos / navigation images
        filename = src.split("/")[-1].split("?")[0]
        if any(x in filename.lower() for x in ["logo", "logotipo", "atalanta_5", "150ppp"]):
            continue

        alt = img.get("alt", "")

        # Find the previous meaningful element in the flow
        prev_el = img
        for _ in range(5):
            prev_el = prev_el.find_previous_sibling()
            if prev_el is None:
                # go up one level
                parent = img.parent
                if parent:
                    prev_el = parent.find_previous_sibling()
                break
            if prev_el.name in ("h1","h2","h3","h4","p","ul","ol","figure","blockquote","pre","div"):
                break

        prev_tag = prev_el.name if prev_el else ""
        prev_text = prev_el.get_text(strip=True)[:100] if prev_el else ""

        images.append({
            "src": src,
            "filename": filename,
            "alt": alt,
            "prev_tag": prev_tag,
            "prev_text": prev_text,
        })

    return images

def download_image(src, filename):
    """Download image to imagenes/ folder. Returns True if downloaded."""
    dest = os.path.join(IMG_DIR, filename)
    if os.path.exists(dest):
        print(f"  [EXISTS] {filename}")
        return False
    try:
        r = requests.get(src, headers=HEADERS, timeout=30)
        r.raise_for_status()
        with open(dest, "wb") as f:
            f.write(r.content)
        print(f"  [DL] {filename}")
        return True
    except Exception as e:
        print(f"  [ERROR] {filename}: {e}")
        return False

def find_element_in_local(soup_local, tag, text_snippet):
    """
    Find the element in local HTML that matches the live site's prev element.
    Returns the Tag or None.
    """
    if not tag or not text_snippet:
        return None

    text_snippet = text_snippet.strip()
    if len(text_snippet) < 5:
        return None

    candidates = soup_local.find_all(tag)
    best = None
    best_score = 0
    # Use first 60 chars of snippet for matching
    key = text_snippet[:60].lower()
    for el in candidates:
        el_text = el.get_text(strip=True).lower()
        # Score by how much of the key appears in el_text
        overlap = sum(1 for c in key if c in el_text)
        # Also check substring
        if key[:30] in el_text:
            overlap += 50
        if overlap > best_score:
            best_score = overlap
            best = el

    if best_score < 15:
        return None
    return best

def already_has_image(el, filename):
    """Check if there's already a figure with this image after the element."""
    next_el = el.find_next_sibling()
    if next_el and next_el.name == "figure":
        img = next_el.find("img")
        if img and filename in img.get("src", ""):
            return True
    return False

def figure_html(filename, alt=""):
    indent = "          "
    return (
        f'\n{indent}<figure class="article-content-image">\n'
        f'{indent}  <img src="imagenes/{filename}" alt="{alt}">\n'
        f'{indent}</figure>'
    )

def update_local_html(html_file, images):
    """
    Update local HTML file by inserting figure elements after the correct elements.
    Works on raw string to preserve formatting.
    """
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse with BS4 just for finding positions (we'll do string manipulation)
    soup = BeautifulSoup(content, "html.parser")
    article_body = soup.find(class_="article-body")
    if not article_body:
        print(f"  [WARN] No .article-body found in {html_file}")
        return

    # Remove existing placeholder figures that have wrong/placeholder src
    placeholder_pattern = re.compile(
        r'\s*<figure class="article-content-image">\s*<img src="imagenes/[^"]*" alt="[^"]*">\s*</figure>',
        re.MULTILINE
    )
    # We'll handle each image one by one

    inserted = []
    not_found = []

    for img_info in images:
        filename = img_info["filename"]
        alt = img_info["alt"]
        prev_tag = img_info["prev_tag"]
        prev_text = img_info["prev_text"]

        # Check if already present
        if f'imagenes/{filename}' in content:
            print(f"  [SKIP] {filename} already in HTML")
            inserted.append(filename)
            continue

        # Find the insertion point
        match_el = find_element_in_local(soup, prev_tag, prev_text)
        if not match_el:
            # Try with less specific tags
            for fallback_tag in ["h2","h3","p"]:
                match_el = find_element_in_local(soup, fallback_tag, prev_text)
                if match_el:
                    break

        if not match_el:
            print(f"  [NOT FOUND] {filename} - prev: [{prev_tag}] {prev_text[:50]}")
            not_found.append(img_info)
            continue

        # Find the element's string representation in the raw content
        el_str = str(match_el)
        # Use a unique enough portion to find it
        search_str = el_str[:200] if len(el_str) > 200 else el_str

        # Find the position right after this element in the raw HTML
        idx = content.find(search_str)
        if idx == -1:
            # Try shorter search
            search_str = el_str[:80]
            idx = content.find(search_str)

        if idx == -1:
            print(f"  [NOT FOUND in RAW] {filename}")
            not_found.append(img_info)
            continue

        # Find end of this element in raw content
        end_idx = idx + len(search_str)
        # Find the actual end of this tag's close
        close_tag = f"</{match_el.name}>"
        close_idx = content.find(close_tag, idx)
        if close_idx != -1:
            insert_pos = close_idx + len(close_tag)
        else:
            insert_pos = end_idx

        # Insert the figure
        fig = figure_html(filename, alt)
        content = content[:insert_pos] + fig + content[insert_pos:]
        inserted.append(filename)
        print(f"  [INSERT] {filename} after <{prev_tag}> \"{prev_text[:40]}\"")

        # Re-parse after modification
        soup = BeautifulSoup(content, "html.parser")
        article_body = soup.find(class_="article-body")

    if not_found:
        print(f"  [MANUAL NEEDED] {len(not_found)} images not auto-placed:")
        for img_info in not_found:
            print(f"    - {img_info['filename']} (after: {img_info['prev_text'][:60]})")

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(content)

    return inserted, not_found


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    summary = {}

    for html_file, slug in ARTICLES.items():
        if html_file in SKIP_ARTICLES:
            print(f"\n[SKIP] {html_file}")
            continue

        print(f"\n{'='*60}")
        print(f"Processing: {html_file} -> /{slug}/")

        # Step 1: Fetch live article
        try:
            content_el = get_article_content(slug)
        except Exception as e:
            print(f"  [ERROR] Fetch failed: {e}")
            summary[html_file] = {"error": str(e)}
            continue

        if not content_el:
            print(f"  [WARN] No article content found")
            summary[html_file] = {"images": [], "error": "no content"}
            continue

        # Step 2: Extract images
        images = get_article_images(content_el)
        if not images:
            print(f"  [NO IMAGES] No article images found")
            summary[html_file] = {"images": []}
            continue

        print(f"  Found {len(images)} images:")
        for img in images:
            print(f"    {img['filename']} (after [{img['prev_tag']}]: {img['prev_text'][:50]})")

        # Step 3: Download images
        for img in images:
            download_image(img["src"], img["filename"])
            time.sleep(0.1)

        # Step 4: Update local HTML
        if not os.path.exists(html_file):
            print(f"  [ERROR] Local file not found: {html_file}")
            continue

        result = update_local_html(html_file, images)
        summary[html_file] = {"images": [i["filename"] for i in images]}

    print(f"\n{'='*60}")
    print("SUMMARY:")
    for f, info in summary.items():
        imgs = info.get("images", [])
        err = info.get("error", "")
        print(f"  {f}: {len(imgs)} images{' [ERROR: '+err+']' if err else ''}")

if __name__ == "__main__":
    main()

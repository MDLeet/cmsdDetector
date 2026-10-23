import requests
import sys
import random
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]


def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


CMS_PATTERNS = [
    ("WordPress", [r"wp-content", r"wp-includes", r"wp-admin", r"wordpress", r"xmlrpc\.php"]),
    ("Joomla", [r"Joomla!", r"com_content", r"com_option", r"/media/system/js/", r"mootools-core\.js"]),
    ("Drupal", [r"Drupal", r"sites/all", r"drupal\.org", r"Drupal\.settings"]),
    ("Magento", [r"Log into Magento Admin Page", r'name="dummy" id="dummy"', r"Magento", r"/skin/frontend/"]),
    ("OpenCart", [r"route=product", r"OpenCart", r"route=common", r"catalog/view/theme"]),
    ("PrestaShop", [r"PrestaShop", r"prestashop", r"/modules/ps_"]),
    ("vBulletin", [r"vBulletin", r"vb_meta_bburl", r"vb_login_md5password", r'"baseurl_core"']),
    ("XenForo", [r"xenforo", r"XenForo", r"uix_sidePane_content", r"js/xf/"]),
    ("Moodle", [r"moodle", r"Moodle", r"pluginfile\.php", r"/mod/"]),
    ("Typo3", [r"typo3", r"TYPO3", r"t3lib", r"typo3conf"]),
    ("Contao", [r"contao", r"Contao", r"contao-"]),
    ("ZenCart", [r"zcadmin", r"zencart", r"zen-cart"]),
    ("Mambo", [r"mambo", r"Mambo", r"mambots"]),
    ("Lokomedia", [r"lokomedia", r"Lokomedia"]),
    ("Laravel", [r"laravel_session", r"Laravel"]),
    ("Django", [r"csrfmiddlewaretoken", r"django", r"Django"]),
    ("CodeIgniter", [r"ci_session", r"CodeIgniter"]),
    ("Shopify", [r"cdn\.shopify\.com", r"Shopify"]),
    ("Wix", [r"wix\.com", r"wixstatic\.com"]),
    ("Squarespace", [r"squarespace", r"static1\.squarespace\.com"]),
    ("Ghost", [r"ghost", r'<meta name="generator" content="Ghost']),
    ("DotNetNuke", [r"DotNetNuke", r"DNN", r"dnn_", r"/Portals/", r"/DesktopModules/", r"__dnn", r"\.DOTNETNUKE", r"DNNPersonalization"]),
]


def detect_server_language(url, content, headers):
    detected = []

    powered = headers.get('X-Powered-By', '').lower()
    if 'php' in powered:
        version = re.search(r'php/([\d.]+)', powered)
        detected.append(f"PHP{(' ' + version.group(1)) if version else ''}")
    if 'asp.net' in powered:
        detected.append("ASP.NET")
    if 'express' in powered:
        detected.append("Node.js (Express)")
    if 'servlet' in powered:
        detected.append("Java (Servlet)")

    cookies = headers.get('Set-Cookie', '').lower()
    if 'phpsessid' in cookies and not any('PHP' in d for d in detected):
        detected.append("PHP")
    if 'jsessionid' in cookies and 'Java' not in str(detected):
        detected.append("Java (JSESSIONID)")
    if 'asp.net_sessionid' in cookies and 'ASP.NET' not in str(detected):
        detected.append("ASP.NET")
    if 'laravel_session' in cookies and 'Laravel' not in str(detected):
        detected.append("PHP (Laravel)")

    if re.search(r'\.aspx?(\?|"|\'|\s)', content, re.IGNORECASE):
        if 'ASP.NET' not in str(detected):
            detected.append("ASP.NET (aspx)")
    if re.search(r'\.jsp(\?|"|\'|\s)', content, re.IGNORECASE):
        if 'Java' not in str(detected):
            detected.append("Java (JSP)")
    if re.search(r'\.do(\?|"|\'|\s)', content, re.IGNORECASE):
        if 'Java' not in str(detected):
            detected.append("Java (Struts .do)")
    if re.search(r'\.php(\?|"|\'|\s)', content, re.IGNORECASE):
        if 'PHP' not in str(detected):
            detected.append("PHP")

    return list(dict.fromkeys(detected))


def detect_js_frameworks(content):
    detected = []

    if re.search(r'data-reactroot|data-reactid|__REACT_DEVTOOLS|react\.production\.min\.js|react\.development\.js', content, re.IGNORECASE):
        detected.append("React")

    if re.search(r'/_next/|__NEXT_DATA__|next\.js', content, re.IGNORECASE):
        detected.append("Next.js")
        if "React" not in detected:
            detected.append("React")

    if re.search(r'vue\.js|vue\.min\.js|__VUE__|data-v-[a-f0-9]|v-if=|v-for=', content, re.IGNORECASE):
        detected.append("Vue.js")

    if re.search(r'ng-version|ng-app|angular\.min\.js|angular\.js', content, re.IGNORECASE):
        detected.append("Angular")

    if re.search(r'svelte-|__svelte', content, re.IGNORECASE):
        detected.append("Svelte")

    if re.search(r'__NUXT__|nuxt\.js|/_nuxt/', content, re.IGNORECASE):
        detected.append("Nuxt.js")
        if "Vue.js" not in detected:
            detected.append("Vue.js")

    if re.search(r'gatsby|___gatsby', content, re.IGNORECASE):
        detected.append("Gatsby")

    return detected


def detect_cms(url, content, headers):
    detected = []
    header_text = " ".join([f"{k}: {v}" for k, v in headers.items()])
    searchable = content + " " + header_text

    for cms_name, patterns in CMS_PATTERNS:
        for pattern in patterns:
            try:
                if re.search(pattern, searchable, re.IGNORECASE):
                    if cms_name not in detected:
                        detected.append(cms_name)
                    break
            except re.error:
                continue
    return detected


def check_site(domain):
    if not domain.startswith(('http://', 'https://')):
        url = 'https://' + domain
    else:
        url = domain

    try:
        response = requests.get(
            url,
            headers=get_headers(),
            timeout=15,
            verify=False,
            allow_redirects=True
        )

        if response.status_code < 400:
            server_header = response.headers.get('Server', 'Unknown')
            powered_by = response.headers.get('X-Powered-By', '')
            server_info = server_header
            if powered_by:
                server_info += f" ({powered_by})"

            content = response.text
            cms_list = detect_cms(url, content, response.headers)
            lang_list = detect_server_language(url, content, response.headers)
            js_list = detect_js_frameworks(content)

            return True, server_info, response.status_code, cms_list, lang_list, js_list
        else:
            return False, None, response.status_code, [], [], []
    except requests.exceptions.RequestException:
        return False, None, None, [], [], []


def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
============================================================
   ▄▄▄▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄    ▄▄▄▄▄▄        ▄▄▄▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄   
 ▄▀        ░ ░▒▓░ ▄        ▀▄▄▀      ▀▄   ▄▀▀             ░ ▄              ▀▄ 
▐▌            ░▒▒ █         ▐▌        ▐▌ ▐▌     ▄▄▄▄     ▒▒ █               ▐▌
█              ░▓ ▓                   ░█ █      ░  ░     ░▓ ▓      ▒▀▀░     ░█
▓       ▄▄▄▄▄▄▄▄█ ▒      █▀█  ░▀▄      █ ▒      ▒  ▀▀▀▀▀▀▀▀ ▒      ░  ▒      █
░       █     ·   ░      █ █┼┼▒ █    ┼┼█ ▐▌      ▀▄▄▄▄▄▄    ░      █  █▄     █
█ ┼   ┼ █       · █┼    ┼█ █┼┼▓ █    ┼┼█  ▀▄▄         ┼┼▀▄  █┼┼    █   ░    ┼░
█┼┼┼ ┼┼┼█▄▄▄▄▄▄▄▄ █┼  ┼┼┼█ ▀▀▀▀ █┼  ┼┼┼█     ▀▀▀▀▀▄▄┼├├┼├├▌ █┼┼┼┼ ┼█   ▒  ┼┼┼▒
█┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼░ █┼┼┼┼┼┼░      █┼┼┼┼┼┼░ ▀▀▀▀▀▀▀░  ▒┼├├┼├├▓ █┼┼┼┼┼┼█   ▓┼┼┼┼┼▓
▐▌┼┼┼┼┼┼┼┼┼┼┼┼┼┼▒ █┼┼┼┼┼┼▒      █┼┼┼ ┼┼▒ ▒┼┼├┼┼┼▒▄▄▓┼┼├┼┼▐▌ █┼┼┼┼┼┼█▄▄▄▀┼┼┼┼▐▌
·▀▄┼┼┼┼┼┼┼┼┼┼┼┼┼▓ █┼┼┼┼┼┼▓      █┼┼┼┼┼┼▓ ░┼├┼┼┼┼┼┼┼┼┼┼┼┼▄▀  █┼┼┼┼┼┼┼┼┼┼┼┼┼┼▄▀ 
   ▀▀▀▀▀▀▀▀▀▀▀▀▀▀ ▀▀▀▀▀▀▀▀      ▀▀▀▀▀▀▀▀ ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀   
   Coded By github.com/MDLeet
============================================================
{Colors.RESET}"""
    print(banner)


def process_line(args):
    idx, total, domain = args
    is_live, server_info, status_code, cms_list, lang_list, js_list = check_site(domain)
    return idx, total, domain, is_live, server_info, status_code, cms_list, lang_list, js_list


def main():
    print_banner()

    input_file = input(f"{Colors.YELLOW}{Colors.BOLD}Enter domains file name (e.g. domains.txt): {Colors.RESET}").strip()

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
    except FileNotFoundError:
        print(f"{Colors.RED}[!] Error: File not found.{Colors.RESET}")
        sys.exit(1)

    if not lines:
        print(f"{Colors.RED}[!] Error: File is empty.{Colors.RESET}")
        sys.exit(1)

    try:
        threads_input = input(f"{Colors.YELLOW}{Colors.BOLD}Number of threads [default=10]: {Colors.RESET}").strip()
        num_threads = int(threads_input) if threads_input else 10
        if num_threads < 1:
            num_threads = 1
    except ValueError:
        num_threads = 10

    total = len(lines)
    print(f"\n{Colors.BLUE}[*] Starting scan... Total: {total} | Threads: {num_threads}{Colors.RESET}\n")

    os.makedirs('Result', exist_ok=True)

    live_results = []
    cms_files = {}
    lang_files = {}
    js_files = {}

    tasks = [(i + 1, total, line) for i, line in enumerate(lines)]

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(process_line, task): task for task in tasks}

        for future in as_completed(futures):
            try:
                idx, t, domain, is_live, server_info, status_code, cms_list, lang_list, js_list = future.result()
            except Exception as e:
                print(f"{Colors.RED}[!] Thread error: {e}{Colors.RESET}")
                continue

            prefix = f"{Colors.MAGENTA}[{idx}/{t}]{Colors.RESET}"
            clean_name = domain.replace('https://', '').replace('http://', '').strip('/')

            if is_live:
                parts = [f"{Colors.WHITE}{clean_name}{Colors.RESET}", f"{Colors.CYAN}{server_info}{Colors.RESET}", f"{Colors.GREEN}({status_code}){Colors.RESET}"]

                if cms_list:
                    parts.append(f"{Colors.YELLOW}CMS: {','.join(cms_list)}{Colors.RESET}")
                    for cms in cms_list:
                        cms_files.setdefault(cms, []).append(clean_name)

                if lang_list:
                    parts.append(f"{Colors.BLUE}Lang: {','.join(lang_list)}{Colors.RESET}")
                    for lang in lang_list:
                        lang_files.setdefault(lang, []).append(clean_name)

                if js_list:
                    parts.append(f"{Colors.MAGENTA}JS: {','.join(js_list)}{Colors.RESET}")
                    for js in js_list:
                        js_files.setdefault(js, []).append(clean_name)

                print(f"{prefix} {Colors.GREEN}[LIVE]{Colors.RESET} " + " | ".join(parts))

                result_line = f"{clean_name} | Status: {status_code} | Server: {server_info}"
                if cms_list:
                    result_line += f" | CMS: {','.join(cms_list)}"
                if lang_list:
                    result_line += f" | Lang: {','.join(lang_list)}"
                if js_list:
                    result_line += f" | JS: {','.join(js_list)}"
                live_results.append(result_line)
            else:
                code_display = f"({status_code})" if status_code else ""
                print(f"{prefix} {Colors.RED}[DOWN]{Colors.RESET} {Colors.WHITE}{domain}{Colors.RESET} {Colors.RED}{code_display}{Colors.RESET}")

    if live_results:
        with open('live.txt', 'w', encoding='utf-8') as out_file:
            for res in live_results:
                out_file.write(res + '\n')
        print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Saved {len(live_results)} live sites to live.txt{Colors.RESET}")

    if cms_files:
        print(f"\n{Colors.CYAN}{Colors.BOLD}[*] CMS Results (Result/):{Colors.RESET}")
        for cms, sites in sorted(cms_files.items()):
            filename = os.path.join('Result', f"{cms}.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(sites) + '\n')
            print(f"  {Colors.YELLOW}[{cms}]{Colors.RESET} -> {len(sites)} sites")

    if lang_files:
        print(f"\n{Colors.BLUE}{Colors.BOLD}[*] Server Language Results (Result/Lang/):{Colors.RESET}")
        os.makedirs('Result/Lang', exist_ok=True)
        for lang, sites in sorted(lang_files.items()):
            safe_name = lang.replace(' ', '_').replace('(', '').replace(')', '').replace('.', '')
            filename = os.path.join('Result/Lang', f"{safe_name}.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(sites) + '\n')
            print(f"  {Colors.BLUE}[{lang}]{Colors.RESET} -> {len(sites)} sites")

    if js_files:
        print(f"\n{Colors.MAGENTA}{Colors.BOLD}[*] JS Framework Results (Result/JS/):{Colors.RESET}")
        os.makedirs('Result/JS', exist_ok=True)
        for js, sites in sorted(js_files.items()):
            safe_name = js.replace('.', '').replace(' ', '_')
            filename = os.path.join('Result/JS', f"{safe_name}.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(sites) + '\n')
            print(f"  {Colors.MAGENTA}[{js}]{Colors.RESET} -> {len(sites)} sites")

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[!] Stopped by user.{Colors.RESET}")
        sys.exit(0)

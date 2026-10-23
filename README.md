
```markdown
# CMS Detector & Domain Checker

A multi-threaded Python tool that scans a list of domains, subdomains, or IP addresses to check if they are live, and detects:

- **CMS** (Content Management System) — 22+ platforms including WordPress, Joomla, Drupal, DotNetNuke (DNN), Magento, and more.
- **Server-side Language** — PHP (with version), ASP.NET, Java (JSP/Struts), Node.js.
- **JavaScript Frameworks** — React, Next.js, Vue.js, Nuxt.js, Angular, Svelte, Gatsby.

Results are saved in organized, categorized files for easy analysis.

---

## Features

- Reads domains line-by-line from a `.txt` file.
- Auto-prepends `https://` if the scheme is missing.
- Random **User-Agent** per request (8 real browser agents) to reduce blocking.
- **Multi-threaded** scanning (configurable thread count).
- Colorized terminal output (LIVE / DOWN / CMS / Lang / JS).
- Saves all live sites to `live.txt`.
- Saves per-CMS results to `Result/<CMS>.txt`.
- Saves per-language results to `Result/Lang/<Lang>.txt`.
- Saves per-JS-framework results to `Result/JS/<Framework>.txt`.
- Handles SSL errors, timeouts, redirects, and `Ctrl+C` gracefully.

---

## Requirements

- **Python 3.7+**
- **requests** library

Install the dependency:

```bash
pip install requests
```

Or:

```bash
pip install -r requirements.txt
```

---

## Installation

```bash
git clone https://github.com/yourusername/cmsDetector.git
cd cmsDetector
pip install requests
```

---

## Usage

1. Create a text file containing your targets (one per line). Example `domains.txt`:

```text
example.com
https://testsite.org
sub.domain.net
192.168.1.1
blog.example.com
```

2. Run the script:

```bash
python3 cms.py
```

3. Enter the file name when prompted:

```
Enter domains file name (e.g. domains.txt): domains.txt
```

4. Enter the number of threads (default = 10):

```
Number of threads [default=10]: 20
```

5. Watch the live scan output:

```
[1/5] [LIVE] example.com | Apache/2.4.41 (Ubuntu) | (200) | CMS: WordPress | Lang: PHP 7.4 | JS: React
[2/5] [LIVE] testsite.org | nginx/1.18.0 | (200) | CMS: Laravel | Lang: PHP | JS: Vue.js
[3/5] [LIVE] sub.domain.net | Microsoft-IIS/10.0 | (200) | CMS: DotNetNuke | Lang: ASP.NET
[4/5] [DOWN] 192.168.1.1
[5/5] [LIVE] blog.example.com | cloudflare | (200) | CMS: Ghost | JS: React
```

6. After the scan, results are saved automatically.

---

## Output Structure

```
live.txt
Result/
├── WordPress.txt
├── Joomla.txt
├── Drupal.txt
├── DotNetNuke.txt
├── Laravel.txt
├── ...
├── Lang/
│   ├── PHP_7.4.txt
│   ├── ASPNET.txt
│   ├── Java_JSP.txt
│   └── ...
└── JS/
├── React.txt
├── Nextjs.txt
├── Vuejs.txt
├── Angular.txt
└── ...
```

### `live.txt` format

```
example.com | Status: 200 | Server: Apache/2.4.41 (Ubuntu) | CMS: WordPress | Lang: PHP 7.4 | JS: React
```

---

## Supported Detections

### CMS (22+)

| CMS | Detection Method |
|-----|------------------|
| WordPress | `wp-content`, `wp-admin`, `xmlrpc.php` |
| Joomla | `com_content`, `Joomla!`, `/media/system/js/` |
| Drupal | `sites/all`, `Drupal.settings` |
| **DotNetNuke (DNN)** | `X-DNN` header, `/Portals/`, `/DesktopModules/`, `.DOTNETNUKE` cookie |
| Magento | `Mage.Cookies`, `/skin/frontend/` |
| OpenCart | `route=product`, `catalog/view/theme` |
| PrestaShop | `/modules/ps_`, `var prestashop` |
| vBulletin | `vBulletin.version`, `vb_meta_bburl` |
| XenForo | `js/xf/`, `uix_sidePane_content` |
| Moodle | `pluginfile.php`, `/mod/` |
| Typo3 | `typo3conf`, `t3lib` |
| Contao | `assets/contao` |
| ZenCart | `zcadmin`, `zen-cart` |
| Mambo | `mambots`, `mambo.php` |
| Lokomedia | `lokomedia` |
| Laravel | `laravel_session`, `Laravel` |
| Django | `csrfmiddlewaretoken`, `Django` |
| CodeIgniter | `ci_session` |
| Shopify | `cdn.shopify.com` |
| Wix | `wixstatic.com` |
| Squarespace | `static1.squarespace.com` |
| Ghost | `<meta name="generator" content="Ghost` |

### Server-side Languages

| Language | Detection |
|----------|-----------|
| PHP (with version) | `X-Powered-By: PHP/8.1`, `PHPSESSID` cookie, `.php` URLs |
| ASP.NET | `X-Powered-By: ASP.NET`, `ASP.NET_SessionId`, `.asp`/`.aspx` |
| Java (JSP / Struts) | `JSESSIONID` cookie, `.jsp`, `.do` |
| Node.js (Express) | `X-Powered-By: Express` |

### JavaScript Frameworks

| Framework | Detection |
|-----------|-----------|
| React | `data-reactroot`, `__REACT_DEVTOOLS` |
| Next.js | `/_next/`, `__NEXT_DATA__` (implies React) |
| Vue.js | `vue.min.js`, `__VUE__`, `data-v-*` |
| Nuxt.js | `__NUXT__`, `/_nuxt/` (implies Vue) |
| Angular | `ng-version`, `ng-app` |
| Svelte | `svelte-*`, `__svelte` |
| Gatsby | `___gatsby` |

---

## How It Works

1. **Read targets** — loads domains line by line from the input file, skipping empty lines.
2. **Normalize URL** — adds `https://` if no scheme is present.
3. **Fetch homepage** — sends a GET request with a random User-Agent, timeout of 15s, and follows redirects.
4. **Live check** — a site is considered live if the HTTP status code is below 400.
5. **Detection** — three parallel analyzers run on the response:
- **CMS**: regex patterns matched against HTML body + response headers.
- **Language**: checks `X-Powered-By`, `Set-Cookie`, and URL extensions.
- **JS frameworks**: regex patterns matched against the HTML source.
6. **Save results** — writes to `live.txt` and categorized files under `Result/`.

---

## Notes and Limitations

- **Passive detection** — the script only fetches the homepage. It does not brute-force admin paths, keeping it lightweight and non-intrusive.
- **SPA limitation** — sites rendered entirely via JavaScript (e.g., pure React SPA with no server-side rendering) may hide CMS/language/framework fingerprints from the initial HTML.
- **Hidden headers** — some servers strip `X-Powered-By` or `Server` headers for security reasons. Results may show `Unknown`.
- **False positives** — patterns like `/Portals/` can theoretically match unrelated sites. Use results as indicators, not absolute proof.
- **Cloudflare/WAF** — fronted sites may return a 403 or challenge page instead of the real content, affecting detection accuracy.

---

## Legal Disclaimer

This tool is intended for **educational purposes** and for scanning domains **you own or have explicit permission to test**. Scanning third-party systems without authorization may violate laws in your country (e.g., Computer Fraud and Abuse Act, GDPR, local cybersecurity regulations). The author assumes no responsibility for misuse.

---

## License

MIT License — free to use, modify, and distribute with attribution.

---

## Contributing

Pull requests are welcome. To add a new CMS, language, or JS framework:

1. Add the pattern to `CMS_PATTERNS` or the relevant detection function.
2. Test on real sites.
3. Submit a PR with a clear description.

---

## Author

Developed for security researchers and web analysts.

Report issues via GitHub Issues.
```

### `requirements.txt`

```text
requests>=2.28.0
urllib3>=1.26.0
```

### Project structure

```
cmsDetector/
├── cms.py
├── README.md
├── requirements.txt
├── domains.txt          # example input
├── live.txt             # generated automatically
└── Result/              # generated automatically
├── WordPress.txt
├── DotNetNuke.txt
├── Lang/
└── JS/
```

from __future__ import annotations

from pathlib import Path


CUSTOM_IFRAME_RESIZE_JS = r"""
(function () {
  const processed = new WeakSet();

  function isHtmlAttachmentFrame(frame) {
    if (!(frame instanceof HTMLIFrameElement)) {
      return false;
    }

    const src = frame.getAttribute("src") || "";
    const sandbox = frame.getAttribute("sandbox") || "";
    return (
      src.startsWith("blob:") ||
      src.includes("attachment") ||
      src.includes(".html") ||
      src.includes("text/html") ||
      sandbox.includes("allow-same-origin")
    );
  }

  function maxDocumentHeight(doc) {
    const body = doc.body;
    const root = doc.documentElement;
    return Math.max(
      body ? body.scrollHeight : 0,
      body ? body.offsetHeight : 0,
      root ? root.clientHeight : 0,
      root ? root.scrollHeight : 0,
      root ? root.offsetHeight : 0,
    );
  }

  function stretchAncestors(frame) {
    let node = frame.parentElement;
    let depth = 0;

    while (node && node !== document.body && depth < 6) {
      node.classList.add("allure-html-attachment-node");
      node.style.width = "100%";
      node.style.maxWidth = "100%";
      node.style.maxHeight = "none";
      node.style.minHeight = depth < 2 ? "80vh" : "0";
      node.style.height = depth < 2 ? "80vh" : "auto";
      node.style.display = "flex";
      node.style.flex = "1 1 auto";
      node.style.flexDirection = "column";
      node.style.justifyContent = "flex-start";
      node.style.alignItems = "stretch";
      node.style.alignSelf = "stretch";
      node.style.paddingTop = "0";
      node.style.marginTop = "0";

      if (depth === 0) {
        node.style.overflow = "visible";
      } else if (depth >= 1 && depth <= 4) {
        node.style.overflowX = "hidden";
        node.style.overflowY = "auto";
      }

      if (depth === 2 || depth === 3) {
        node.classList.add("allure-html-attachment-dialog");
      }

      node = node.parentElement;
      depth += 1;
    }
  }

  function resizeFrame(frame) {
    try {
      const doc = frame.contentDocument;
      if (!doc) {
        return;
      }

      const height = Math.max(maxDocumentHeight(doc), 480);
      frame.style.height = height + "px";
      frame.style.minHeight = "80vh";
      frame.style.width = "100%";
      frame.style.maxHeight = "none";
      frame.style.overflow = "hidden";
      frame.style.display = "block";
      frame.style.flex = "1 1 auto";
      frame.style.background = "#fff";
      frame.setAttribute("scrolling", "no");
      stretchAncestors(frame);
    } catch (error) {
      console.debug("Allure iframe resize skipped:", error);
    }
  }

  function bindFrame(frame) {
    if (!isHtmlAttachmentFrame(frame) || processed.has(frame)) {
      return;
    }
    processed.add(frame);

    const onLoad = function () {
      resizeFrame(frame);

      try {
        const doc = frame.contentDocument;
        if (!doc) {
          return;
        }

        const observer = new ResizeObserver(function () {
          resizeFrame(frame);
        });

        if (doc.body) {
          observer.observe(doc.body);
        }
        if (doc.documentElement) {
          observer.observe(doc.documentElement);
        }
      } catch (error) {
        console.debug("Allure iframe observer skipped:", error);
      }
    };

    frame.addEventListener("load", onLoad);
    setTimeout(onLoad, 50);
    setTimeout(onLoad, 250);
    setTimeout(onLoad, 1000);
  }

  function scan(root) {
    if (!root) {
      return;
    }

    if (root instanceof HTMLIFrameElement) {
      bindFrame(root);
      return;
    }

    if (root.querySelectorAll) {
      root.querySelectorAll("iframe").forEach(bindFrame);
    }
  }

  const observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(scan);
    });
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
  });

  scan(document);
})();
""".strip()


CUSTOM_STYLES_CSS = r"""
iframe[src*="attachment"],
iframe[src*=".html"],
iframe[src^="blob:"][sandbox*="allow-same-origin"] {
  width: 100% !important;
  max-width: 100% !important;
  max-height: none !important;
  min-height: 80vh !important;
  border: 0 !important;
  background: #fff !important;
  display: block !important;
  flex: 1 1 auto !important;
}

.allure-html-attachment-dialog {
  width: min(96vw, 1800px) !important;
  max-width: min(96vw, 1800px) !important;
  max-height: 96vh !important;
}

.allure-html-attachment-node {
  width: 100% !important;
  max-width: 100% !important;
  max-height: none !important;
  justify-content: flex-start !important;
  align-items: stretch !important;
  padding-top: 0 !important;
  margin-top: 0 !important;
}

div:has(> iframe[src^="blob:"][sandbox*="allow-same-origin"]) {
  display: flex !important;
  flex: 1 1 auto !important;
  flex-direction: column !important;
  justify-content: flex-start !important;
  align-items: stretch !important;
  min-height: 80vh !important;
  max-height: none !important;
  width: 100% !important;
  padding-top: 0 !important;
  margin-top: 0 !important;
}

.allure-html-attachment-dialog [class*="modal"],
.allure-html-attachment-dialog [class*="dialog"],
.allure-html-attachment-dialog [class*="content"],
.allure-html-attachment-dialog [class*="panel"],
.allure-html-attachment-dialog [class*="body"] {
  max-height: 96vh !important;
  height: auto !important;
}

.allure-html-attachment-dialog [class*="header"] + div,
.allure-html-attachment-dialog [class*="data"],
.allure-html-attachment-dialog [class*="component"] {
  flex: 1 1 auto !important;
  min-height: 80vh !important;
  max-height: none !important;
  justify-content: flex-start !important;
  align-items: stretch !important;
  padding-top: 0 !important;
  margin-top: 0 !important;
}

.allure-html-attachment-dialog[class*="modal-wrapper__"],
.allure-html-attachment-dialog [class*="modal-wrapper__"],
.allure-html-attachment-dialog [class*="modal-content__"] {
  justify-content: flex-start !important;
  align-items: stretch !important;
}

.allure-html-attachment-dialog [class*="modal-data__"] {
  align-items: flex-start !important;
  justify-content: flex-start !important;
  overflow-x: hidden !important;
  overflow-y: auto !important;
}

.allure-html-attachment-dialog [class*="modal-data-component__"] {
  height: auto !important;
  min-height: 80vh !important;
  max-height: none !important;
  width: 100% !important;
  overflow-x: hidden !important;
  overflow-y: auto !important;
}

.allure-html-attachment-dialog [class*="html-attachment-preview__"] {
  padding: 0 !important;
  margin: 0 !important;
  width: 100% !important;
  overflow: visible !important;
}

.allure-html-attachment-dialog [class*="modal-wrapper__"],
.allure-html-attachment-dialog [class*="modal-content__"] {
  overflow-x: hidden !important;
  overflow-y: auto !important;
}

.allure-html-attachment-dialog iframe[src^="blob:"][sandbox*="allow-same-origin"] {
  margin-top: 0 !important;
  align-self: stretch !important;
}

.allure-html-attachment-dialog h1,
.allure-html-attachment-dialog h2,
.allure-html-attachment-dialog h3,
.allure-html-attachment-dialog h4,
.allure-html-attachment-dialog h5,
.allure-html-attachment-dialog h6,
.allure-html-attachment-dialog p {
  margin-top: 0 !important;
}
""".strip()


def patch_allure_report(report_dir: str | Path) -> bool:
    report_path = Path(report_dir)
    index_path = report_path / "index.html"
    if not index_path.exists():
        return False

    styles_path = report_path / "custom-styles.css"
    script_path = report_path / "custom-iframe-resize.js"

    styles_path.write_text(CUSTOM_STYLES_CSS + "\n", encoding="utf-8")
    script_path.write_text(CUSTOM_IFRAME_RESIZE_JS + "\n", encoding="utf-8")

    index_html = index_path.read_text(encoding="utf-8")

    style_tag = '<link rel="stylesheet" href="./custom-styles.css">'
    script_tag = '<script defer src="./custom-iframe-resize.js"></script>'

    updated_html = index_html
    if style_tag not in updated_html and "</head>" in updated_html:
        updated_html = updated_html.replace("</head>", f"    {style_tag}\n</head>", 1)
    if script_tag not in updated_html and "</body>" in updated_html:
        updated_html = updated_html.replace("</body>", f"    {script_tag}\n</body>", 1)

    if updated_html != index_html:
        index_path.write_text(updated_html, encoding="utf-8")

    return True

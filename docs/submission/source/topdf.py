# Open a .docx in LibreOffice (UNO), update the TOC and other indexes, export PDF.
import sys, time, subprocess, uno
from com.sun.star.beans import PropertyValue
def pv(n, v):
    p = PropertyValue(); p.Name = n; p.Value = v; return p
src, out, soffice, profile = sys.argv[1:5]
proc = subprocess.Popen([soffice, "--headless", "--invisible", "--norestore", f"-env:UserInstallation=file://{profile}",
                         "--accept=socket,host=127.0.0.1,port=2099;urp;"])
ctx = None
for _ in range(60):
    try:
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
        ctx = resolver.resolve("uno:socket,host=127.0.0.1,port=2099;urp;StarOffice.ComponentContext"); break
    except Exception: time.sleep(1)
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.loadComponentFromURL(uno.systemPathToFileUrl(src), "_blank", 0, (pv("Hidden", True),))
idx = doc.getDocumentIndexes()
for i in range(idx.getCount()): idx.getByIndex(i).update()
doc.refresh()
doc.storeToURL(uno.systemPathToFileUrl(out), (pv("FilterName", "writer_pdf_Export"),))
doc.close(True)
try: desktop.terminate()
except Exception: pass
proc.wait(timeout=30)
print("pdf", out, "indexes", idx.getCount())

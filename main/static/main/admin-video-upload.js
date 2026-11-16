(() => {
  const form = document.querySelector("#coursevideo_form");
  const fileInput = form?.querySelector('input[type="file"]');

  if (!form || !fileInput) {
    return;
  }

  const status = document.createElement("p");
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");
  status.hidden = true;
  status.style.cssText =
    "margin: 12px 0; padding: 12px; border-radius: 6px; background: #e8f4ff; color: #102a43;";
  form.parentNode.insertBefore(status, form);

  form.addEventListener("submit", (event) => {
    const file = fileInput.files?.[0];
    if (!file || !window.XMLHttpRequest) {
      return;
    }

    event.preventDefault();

    const submitter = event.submitter;
    const data = new FormData(form);
    if (submitter?.name) {
      data.append(submitter.name, submitter.value);
    }

    const xhr = new XMLHttpRequest();
    const submitButtons = form.querySelectorAll(
      'button[type="submit"], input[type="submit"]',
    );
    const startedAt = Date.now();

    status.hidden = false;
    status.textContent = `در حال آماده‌سازی ارسال «${file.name}»...`;
    submitButtons.forEach((button) => {
      button.disabled = true;
    });

    xhr.open(form.method || "POST", form.action || window.location.href);
    xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");

    xhr.upload.addEventListener("progress", (progressEvent) => {
      if (!progressEvent.lengthComputable) {
        status.textContent = `در حال بارگذاری «${file.name}»...`;
        return;
      }

      const percent = Math.round(
        (progressEvent.loaded / progressEvent.total) * 100,
      );
      const uploadedMb = (progressEvent.loaded / (1024 * 1024)).toFixed(1);
      const totalMb = (progressEvent.total / (1024 * 1024)).toFixed(1);
      const elapsedSeconds = Math.max((Date.now() - startedAt) / 1000, 1);
      const bytesPerSecond = progressEvent.loaded / elapsedSeconds;
      const remainingSeconds =
        bytesPerSecond > 0
          ? Math.ceil(
              (progressEvent.total - progressEvent.loaded) / bytesPerSecond,
            )
          : null;
      const remainingText =
        remainingSeconds === null
          ? ""
          : ` - حدود ${remainingSeconds} ثانیه باقی‌مانده`;

      status.textContent =
        percent === 100
          ? "ارسال فایل تمام شد؛ در حال ذخیره در سامانه..."
          : `در حال بارگذاری: ${percent}٪ (${uploadedMb} از ${totalMb} مگابایت)${remainingText}`;
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        if (
          xhr.responseText.includes('class="errornote"') ||
          xhr.responseText.includes('class="errorlist"')
        ) {
          document.open();
          document.write(xhr.responseText);
          document.close();
          return;
        }

        window.location.assign(xhr.responseURL || form.action);
        return;
      }

      status.textContent = `ذخیره ویدیو ناموفق بود (خطای ${xhr.status}). اتصال را بررسی کنید و دوباره تلاش کنید.`;
      submitButtons.forEach((button) => {
        button.disabled = false;
      });
    });

    xhr.addEventListener("error", () => {
      status.textContent =
        "ارتباط هنگام ارسال قطع شد. اتصال را بررسی کنید و دوباره تلاش کنید.";
      submitButtons.forEach((button) => {
        button.disabled = false;
      });
    });

    xhr.send(data);
  });
})();

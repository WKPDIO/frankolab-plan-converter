// drop zones, loading state, copy-to-clipboard. No frameworks, no tracking.
(function () {
  function sizeText(n) {
    return n > 1048576 ? (n / 1048576).toFixed(1).replace(".", ",") + " МБ" : Math.max(1, Math.round(n / 1024)) + " КБ";
  }

  var form = document.getElementById("convert");
  if (form) {
    var submit = form.querySelector("[data-submit]");
    var zones = form.querySelectorAll("[data-drop]");

    function refresh() {
      var pdf = form.querySelector('input[name="plan"]');
      submit.disabled = !(pdf.files && pdf.files.length);
    }

    zones.forEach(function (zone) {
      var input = zone.querySelector('input[type="file"]');
      var name = zone.querySelector("[data-name]");
      var sub = zone.querySelector("[data-sub]");
      var defName = name.textContent, defSub = sub.textContent;

      function show() {
        var f = input.files && input.files[0];
        zone.classList.toggle("has", !!f);
        name.textContent = f ? f.name : defName;
        sub.textContent = f ? sizeText(f.size) : defSub;
        refresh();
      }
      input.addEventListener("change", show);
      ["dragenter", "dragover"].forEach(function (ev) {
        zone.addEventListener(ev, function (e) { e.preventDefault(); zone.classList.add("over"); });
      });
      ["dragleave", "drop"].forEach(function (ev) {
        zone.addEventListener(ev, function () { zone.classList.remove("over"); });
      });
      zone.addEventListener("drop", function (e) {
        e.preventDefault();
        if (e.dataTransfer && e.dataTransfer.files.length) {
          input.files = e.dataTransfer.files;
          show();
        }
      });
      zone.querySelector("[data-clear]").addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        input.value = "";
        show();
      });
      show();
    });

    // a PDF dropped anywhere on the page goes to the plan field
    document.addEventListener("dragover", function (e) { e.preventDefault(); });
    document.addEventListener("drop", function (e) {
      if (e.target.closest && e.target.closest("[data-drop]")) return;
      e.preventDefault();
      var f = e.dataTransfer && e.dataTransfer.files[0];
      if (!f) return;
      var target = /pdf$/i.test(f.type) || /\.pdf$/i.test(f.name) ? 'input[name="plan"]' : 'input[name="pano"]';
      var input = form.querySelector(target);
      input.files = e.dataTransfer.files;
      input.dispatchEvent(new Event("change"));
    });

    form.addEventListener("submit", function () {
      submit.disabled = true;
      document.querySelector("[data-busy]").classList.add("on");
    });
    // back button after a redirect: never leave the overlay on
    window.addEventListener("pageshow", function () {
      document.querySelector("[data-busy]").classList.remove("on");
      refresh();
    });
  }

  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var el = document.getElementById(btn.getAttribute("data-copy"));
      var text = Array.prototype.map.call(el.querySelectorAll("li"), function (li) { return li.textContent; }).join("\n");
      navigator.clipboard.writeText(text).then(function () {
        var old = btn.textContent;
        btn.textContent = "Скопійовано";
        setTimeout(function () { btn.textContent = old; }, 1600);
      });
    });
  });
})();

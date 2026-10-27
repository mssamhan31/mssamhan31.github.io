/* Four small behaviours, no framework: mobile nav, side-nav scroll-spy, gallery lightbox,
   and the CV level-of-detail switch. */
(function () {
  "use strict";

  // Mobile navigation
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
    });
  }

  // Highlight the side-nav link for the heading currently in view
  var links = Array.prototype.slice.call(document.querySelectorAll(".toc a[href^='#']"));
  if (links.length && "IntersectionObserver" in window) {
    var byId = {};
    links.forEach(function (a) { byId[a.getAttribute("href").slice(1)] = a; });
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) { return; }
        links.forEach(function (a) { a.classList.remove("is-active"); });
        var active = byId[entry.target.id];
        if (active) { active.classList.add("is-active"); }
      });
    }, { rootMargin: "-15% 0px -75% 0px" });
    Object.keys(byId).forEach(function (id) {
      var target = document.getElementById(id);
      if (target) { observer.observe(target); }
    });
  }

  // Gallery lightbox
  var box = document.querySelector(".lightbox");
  if (box) {
    var image = box.querySelector("img");
    var caption = box.querySelector("p");
    document.querySelectorAll(".gallery figure").forEach(function (figure) {
      figure.addEventListener("click", function () {
        image.src = figure.getAttribute("data-full") || figure.querySelector("img").src;
        image.alt = figure.querySelector("figcaption").textContent;
        caption.textContent = image.alt;
        box.classList.add("is-open");
      });
    });
    var close = function () { box.classList.remove("is-open"); };
    box.addEventListener("click", close);
    document.addEventListener("keydown", function (event) { if (event.key === "Escape") { close(); } });
  }

  // CV level of detail: Featured, Normal or Full detail. Sections with nothing left to show hide.
  var cv = document.querySelector(".cv");
  var buttons = Array.prototype.slice.call(document.querySelectorAll(".view-switch button"));
  if (cv && buttons.length) {
    var apply = function (view) {
      cv.setAttribute("data-view", view);
      buttons.forEach(function (b) { b.classList.toggle("is-active", b.getAttribute("data-view") === view); });
      document.querySelectorAll(".hide-when-empty").forEach(function (group) {
        var rows = Array.prototype.slice.call(group.querySelectorAll("[data-show]"));
        var visible = rows.some(function (row) { return getComputedStyle(row).display !== "none"; });
        group.classList.toggle("is-empty", !visible);
      });
    };
    buttons.forEach(function (b) {
      b.addEventListener("click", function () { apply(b.getAttribute("data-view")); });
    });
    var requested = new URLSearchParams(window.location.search).get("view");
    var known = buttons.some(function (b) { return b.getAttribute("data-view") === requested; });
    apply(known ? requested : cv.getAttribute("data-view"));
  }
})();

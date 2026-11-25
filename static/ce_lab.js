/**
 * CE Lab tab controller (Task 5).
 *
 * Wires the server-rendered ARIA tablist on /ce-lab. No dependencies.
 * - Click or ArrowLeft/ArrowRight/Home/End moves activation.
 * - Activation updates aria-selected, tabindex, panel visibility, and the
 *   single hidden `analysis` input. It never submits the form; the user must
 *   click "Run Simulation".
 * - On load, syncs the UI to the hidden input's current value so a POST that
 *   returned e.g. analysis="ac" shows the AC tab before any interaction.
 */
(function () {
  "use strict";

  function init() {
    var tablist = document.querySelector('.ce-lab-tabs[role="tablist"]');
    if (!tablist) {
      return;
    }

    var tabs = Array.prototype.slice.call(tablist.querySelectorAll('[role="tab"]'));
    if (tabs.length === 0) {
      return;
    }

    var hiddenInput = document.getElementById("analysis");

    function panelFor(tab) {
      var panelId = tab.getAttribute("aria-controls");
      if (!panelId) {
        return null;
      }
      return document.getElementById(panelId);
    }

    function setActive(tab, focus) {
      var activeAnalysis = tab.getAttribute("data-analysis") || "";

      tabs.forEach(function (t) {
        var selected = t === tab;
        t.setAttribute("aria-selected", selected ? "true" : "false");
        t.setAttribute("tabindex", selected ? "0" : "-1");
      });

      tabs.forEach(function (t) {
        var panel = panelFor(t);
        if (panel) {
          panel.hidden = t.getAttribute("data-analysis") !== activeAnalysis;
        }
      });

      if (hiddenInput) {
        hiddenInput.value = activeAnalysis;
      }

      if (focus) {
        tab.focus();
      }
    }

    function handleKeydown(event) {
      var currentIndex = tabs.indexOf(document.activeElement);
      var nextIndex = null;

      if (event.key === "ArrowRight") {
        nextIndex = currentIndex + 1;
      } else if (event.key === "ArrowLeft") {
        nextIndex = currentIndex - 1;
      } else if (event.key === "Home") {
        nextIndex = 0;
      } else if (event.key === "End") {
        nextIndex = tabs.length - 1;
      } else {
        return;
      }

      event.preventDefault();
      var nextTab = tabs[(nextIndex + tabs.length) % tabs.length];
      setActive(nextTab, true);
    }

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        setActive(tab, true);
      });
      tab.addEventListener("keydown", handleKeydown);
    });

    function syncFromHidden() {
      var initialTab = tabs[0];
      if (hiddenInput && hiddenInput.value) {
        var match = null;
        tabs.forEach(function (t) {
          if (t.getAttribute("data-analysis") === hiddenInput.value) {
            match = t;
          }
        });
        if (match) {
          initialTab = match;
        }
      }
      setActive(initialTab, false);
    }

    syncFromHidden();
  }

  function start() {
    init();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();

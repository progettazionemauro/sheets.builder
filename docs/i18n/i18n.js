
/* Djungo i18n — UAT-F44 */
(function () {
  "use strict";

  const LANGUAGES = ["en", "it"];
  const STORAGE_KEY = "DJUNGO_LANGUAGE";
  const dictionaries = {};

  function preferredLanguage() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (LANGUAGES.includes(saved)) return saved;
    } catch (_) {}

    const browser = String(
      navigator.language || "en"
    ).toLowerCase();

    return browser.startsWith("it") ? "it" : "en";
  }

  let language = preferredLanguage();

  function t(key) {
    return dictionaries[language]?.[key]
      ?? dictionaries.en?.[key]
      ?? key;
  }

  function apply() {
    document.documentElement.lang = language;

    document.querySelectorAll("[data-i18n]").forEach(el => {
      el.textContent = t(el.dataset.i18n);
    });

    document.querySelectorAll(
      "[data-i18n-placeholder]"
    ).forEach(el => {
      el.placeholder = t(el.dataset.i18nPlaceholder);
    });

    document.querySelectorAll(
      "[data-i18n-title]"
    ).forEach(el => {
      el.title = t(el.dataset.i18nTitle);
    });

    document.querySelectorAll(
      "[data-djungo-language-select]"
    ).forEach(el => {
      el.value = language;
    });

    window.dispatchEvent(
      new CustomEvent("djungo-language-changed", {
        detail: {language}
      })
    );
  }

  function setLanguage(next, persist = true) {
    if (!LANGUAGES.includes(next)) return false;

    language = next;

    if (persist) {
      try {
        localStorage.setItem(STORAGE_KEY, language);
      } catch (_) {}
    }

    apply();
    return true;
  }

  function mountSelector(host) {
    if (!host) return;

    const label = document.createElement("label");
    label.textContent = t("language") + ": ";
    label.style.marginRight = "8px";

    const select = document.createElement("select");
    select.dataset.djungoLanguageSelect = "true";
    select.setAttribute("aria-label", "Language / Lingua");

    [
      ["en", "English"],
      ["it", "Italiano"]
    ].forEach(([value, caption]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = caption;
      select.appendChild(option);
    });

    select.value = language;

    select.addEventListener("change", () => {
      setLanguage(select.value);
    });

    host.append(label, select);

    window.addEventListener(
      "djungo-language-changed",
      () => {
        label.textContent = t("language") + ": ";
      }
    );
  }

  window.addEventListener("storage", event => {
    if (event.key === STORAGE_KEY) {
      setLanguage(preferredLanguage(), false);
    }
  });

  const ready = Promise.all(
    LANGUAGES.map(async code => {
      const response = await fetch(
        "/i18n/" + code + ".json",
        {cache: "no-cache"}
      );

      if (!response.ok) {
        throw new Error("Cannot load dictionary: " + code);
      }

      dictionaries[code] = await response.json();
    })
  ).then(() => {
    apply();
    return true;
  });

  window.DjungoI18n = {
    t,
    apply,
    setLanguage,
    getLanguage: () => language,
    mountSelector,
    ready
  };
})();

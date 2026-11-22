import { useEffect } from "react";

const APP_NAME = "Fake Music Hunter";

/**
 * Fija el título de la pestaña como `<título> · Fake Music Hunter`
 * y restaura el anterior al desmontar la página.
 */
export function useDocumentTitle(title: string) {
  useEffect(() => {
    const previous = document.title;
    document.title = `${title} · ${APP_NAME}`;
    return () => {
      document.title = previous;
    };
  }, [title]);
}

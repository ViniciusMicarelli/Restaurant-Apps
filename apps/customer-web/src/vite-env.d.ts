/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_RESTAURANT_SERVICE_URL: string;
  readonly VITE_MENU_SERVICE_URL: string;
  readonly VITE_DINING_SERVICE_URL: string;
  readonly VITE_ORDER_SERVICE_URL: string;
  readonly VITE_DEFAULT_RESTAURANT_SLUG?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

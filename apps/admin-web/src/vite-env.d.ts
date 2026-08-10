/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AUTH_SERVICE_URL: string;
  readonly VITE_RESTAURANT_SERVICE_URL: string;
  readonly VITE_DINING_SERVICE_URL: string;
  readonly VITE_KITCHEN_SERVICE_URL: string;
  readonly VITE_KITCHEN_WS_URL: string;
  readonly VITE_ORDER_SERVICE_URL: string;
  readonly VITE_PAYMENT_SERVICE_URL: string;
  readonly VITE_NOTIFICATION_SERVICE_URL: string;
  readonly VITE_CUSTOMER_WEB_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

import { createBrowserRouter } from "react-router-dom";

import { CatalogPage } from "../features/catalog/CatalogPage";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { RfqExtractPage } from "../features/rfq/RfqExtractPage";
import { QuotationPage } from "../features/quotation/QuotationPage";
import { SalesDashboard } from "../features/sales/SalesDashboard";
import { ValidationPage } from "../features/validation/ValidationPage";
import { AppLayout } from "../shared/layout/AppLayout";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <SalesDashboard />,
      },
      {
        path: "sales",
        element: <SalesDashboard />,
      },
      {
        path: "dashboard",
        element: <DashboardPage />,
      },
      {
        path: "catalog",
        element: <CatalogPage />,
      },
      {
        path: "rfq",
        element: <RfqExtractPage />,
      },
      {
        path: "validation",
        element: <ValidationPage />,
      },
      {
        path: "quotation",
        element: <QuotationPage />,
      },
    ],
  },
]);

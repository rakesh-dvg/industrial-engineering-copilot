import { useQuery } from "@tanstack/react-query";

import { fetchProducts } from "../../api/products";

export function CatalogPage() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["catalog", "products"],
    queryFn: fetchProducts,
  });

  if (isLoading) {
    return <p>Loading product catalog…</p>;
  }

  if (isError) {
    return <p role="alert">Failed to load catalog: {(error as Error).message}</p>;
  }

  return (
    <section aria-labelledby="catalog-heading">
      <h2 id="catalog-heading">Product Catalog</h2>
      <p>{data?.total ?? 0} synthetic products available for engineering workflows.</p>
      <ul className="catalog-list">
        {data?.items.map((product) => (
          <li key={product.id}>
            <strong>{product.model_number}</strong> — {product.name}
            <div className="catalog-meta">
              {product.manufacturer.name} · {product.category.name}
              {product.pricing ? (
                <span>
                  {" "}
                  · {product.pricing.currency} {product.pricing.unit_price}
                </span>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

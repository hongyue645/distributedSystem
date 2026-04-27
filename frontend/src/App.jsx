import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const CATEGORY_OPTIONS = [
  "Electronics",
  "Clothing",
  "Accessories",
  "Keys",
  "Books",
  "Bags",
  "Other",
];

const initialForm = {
  item_type: "lost",
  name: "",
  category: "Electronics",
  color: "",
};

function App() {
  const [form, setForm] = useState(initialForm);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitStatus, setSubmitStatus] = useState("");
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  async function fetchItems() {
    try {
      const response = await fetch(`${API_URL}/items`);

      if (!response.ok) {
        throw new Error("Failed to fetch items from Gateway API");
      }

      const result = await response.json();
      setItems(result.data || []);
      setLastUpdated(new Date());
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    fetchItems();

    const timer = setInterval(() => {
      fetchItems();
    }, 3000);

    return () => clearInterval(timer);
  }, []);

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((previousForm) => ({
      ...previousForm,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setSubmitStatus("");
    setError("");

    try {
      const response = await fetch(`${API_URL}/items`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(form),
      });

      if (!response.ok) {
        const errorBody = await response.json();
        throw new Error(errorBody.detail || "Failed to submit item");
      }

      setSubmitStatus("Item submitted successfully. The matching worker will check it in the background.");
      setForm(initialForm);
      await fetchItems();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const openItems = useMemo(() => {
    return items.filter((item) => item.status === "open");
  }, [items]);

  const matchedItems = useMemo(() => {
    return items.filter((item) => item.status === "matched");
  }, [items]);

  const lostCount = items.filter((item) => item.item_type === "lost").length;
  const foundCount = items.filter((item) => item.item_type === "found").length;

  return (
    <main className="app">
      <section className="hero">
        <div>
          <h1>Campus Lost & Found</h1>
        </div>
      </section>

      <section className="dashboard">
        <article className="panel form-panel">
          <h2>Report an Item</h2>
          <form onSubmit={handleSubmit}>
            <label>
              Item Type
              <select name="item_type" value={form.item_type} onChange={handleChange}>
                <option value="lost">Lost</option>
                <option value="found">Found</option>
              </select>
            </label>

            <label>
              Item Name
              <input
                name="name"
                value={form.name}
                onChange={handleChange}
                placeholder="Example: Apple MacBook Pro"
                required
              />
            </label>

            <label>
              Category
              <select name="category" value={form.category} onChange={handleChange}>
                {CATEGORY_OPTIONS.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Color
              <input
                name="color"
                value={form.color}
                onChange={handleChange}
                placeholder="Example: Silver"
                required
              />
            </label>

            <button type="submit" disabled={loading}>
              {loading ? "Submitting..." : "Submit Item"}
            </button>
          </form>

          {submitStatus && <p className="success">{submitStatus}</p>}
          {error && <p className="error">{error}</p>}
        </article>

        <article className="panel stats-panel">
          <h2>Live System Status</h2>

          <div className="stats-grid">
            <div>
              <strong>{items.length}</strong>
              <span>Total Items</span>
            </div>
            <div>
              <strong>{openItems.length}</strong>
              <span>Open Items</span>
            </div>
            <div>
              <strong>{matchedItems.length}</strong>
              <span>Matched Items</span>
            </div>
            <div>
              <strong>{lostCount}</strong>
              <span>Lost Reports</span>
            </div>
            <div>
              <strong>{foundCount}</strong>
              <span>Found Reports</span>
            </div>
          </div>

          <p className="last-updated">
            Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : "Loading..."}
          </p>

          <button className="secondary-button" onClick={fetchItems}>
            Refresh Now
          </button>
        </article>
      </section>

      <section className="items-section">
        <ItemList title="Open Items" items={openItems} emptyText="No open items." />
        <ItemList title="Matched Items" items={matchedItems} emptyText="No matched items yet." />
      </section>
    </main>
  );
}

function ItemList({ title, items, emptyText }) {
  return (
    <article className="panel">
      <h2>{title}</h2>

      {items.length === 0 ? (
        <p className="empty">{emptyText}</p>
      ) : (
        <div className="item-list">
          {items.map((item) => (
            <div className="item-card" key={item.id}>
              <div className="item-card-header">
                <strong>{item.name}</strong>
                <span className={`badge ${item.status}`}>{item.status}</span>
              </div>

              <p>
                <span>Type:</span> {item.item_type}
              </p>
              <p>
                <span>Category:</span> {item.category}
              </p>
              <p>
                <span>Color:</span> {item.color}
              </p>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}

export default App;
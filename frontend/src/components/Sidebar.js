function Sidebar({ items, activePage, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-mark">LL</div>
        <div>
          <strong>LiveLong.ai</strong>
          <p>Healthcare dashboard</p>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Primary">
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`sidebar-link ${activePage === item.id ? 'active' : ''}`}
            onClick={() => onNavigate(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span>System status</span>
        <strong>Online</strong>
      </div>
    </aside>
  );
}

export default Sidebar;

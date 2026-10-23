
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <header className="navbar">
      <Link to="/" className="brand">
        Student Management
      </Link>

      {user && (
        <nav className="nav-links">
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/students">Students</Link>
          <Link to="/courses">Courses</Link>
          <button type="button" onClick={handleLogout}>
            Logout
          </button>
        </nav>
      )}
    </header>
  );
}

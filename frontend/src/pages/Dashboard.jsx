
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { user } = useAuth();

  const displayName =
    user?.name || user?.full_name || user?.email || "User";

  return (
    <main className="page-container">
      <section className="dashboard-welcome">
        <div>
          <p className="eyebrow">OVERVIEW</p>
          <h1>Welcome, {displayName}!</h1>
          <p>
            Manage your student records and courses from one place.
          </p>
        </div>
      </section>

      <section className="dashboard-grid">
        <article className="dashboard-card">
          <div className="dashboard-card-icon students-icon">S</div>
          <h2>Student Management</h2>
          <p>View and manage student records.</p>
          <Link className="dashboard-link" to="/students">
            Manage Students →
          </Link>
        </article>

        <article className="dashboard-card">
          <div className="dashboard-card-icon courses-icon">C</div>
          <h2>Course Management</h2>
          <p>Organize and manage available courses.</p>
          <Link className="dashboard-link" to="/courses">
            Manage Courses →
          </Link>
        </article>
      </section>
    </main>
  );
}

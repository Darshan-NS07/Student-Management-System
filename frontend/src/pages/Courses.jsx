
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";

const emptyForm = {
  title: "",
  code: "",
  description: "",
  instructor: "",
  duration_weeks: "12",
  is_active: true,
};

function validateCourse(form) {
  const errors = {};

  for (const field of ["title", "instructor"]) {
    const value = form[field].trim();

    if (value.length < 2 || !/[a-z]/i.test(value)) {
      errors[field] = "Enter at least 2 characters and include a letter.";
    } else if (!/^[\p{L}\s.'-]+$/u.test(value)) {
      errors[field] = "Contains invalid characters.";
    }
  }

  const code = form.code.trim();

  if (
    code.length < 2 ||
    code.length > 20 ||
    !/^[A-Za-z0-9_-]+$/.test(code)
  ) {
    errors.code = "Use 2–20 letters, numbers, hyphens, or underscores.";
  }

  if (form.description.length > 1000) {
    errors.description = "Description cannot exceed 1000 characters.";
  }

  const duration = Number(form.duration_weeks);

  if (
    !Number.isInteger(duration) ||
    duration < 1 ||
    duration > 520
  ) {
    errors.duration_weeks = "Duration must be between 1 and 520 weeks.";
  }

  return errors;
}

export default function Courses() {
  const [courses, setCourses] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadCourses = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest("/courses/");
      setCourses(Array.isArray(data) ? data : data.courses || []);
    } catch (err) {
      setError(err.message || "Unable to load courses.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCourses();
  }, [loadCourses]);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;

    setForm((current) => ({
      ...current,
      [name]: type === "checkbox" ? checked : value,
    }));

    setErrors((current) => ({ ...current, [name]: "" }));
    setNotice("");
  };

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
    setErrors({});
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const validationErrors = validateCourse(form);
    setErrors(validationErrors);
    setError("");
    setNotice("");

    if (Object.keys(validationErrors).length > 0) return;

    setSaving(true);

    const payload = {
      title: form.title.trim(),
      code: form.code.trim().toUpperCase(),
      description: form.description.trim(),
      instructor: form.instructor.trim(),
      duration_weeks: Number(form.duration_weeks),
    };

    try {
      if (editingId !== null) {
        await apiRequest(`/courses/${editingId}`, {
          method: "PUT",
          body: JSON.stringify({
            ...payload,
            is_active: form.is_active,
          }),
        });

        setNotice("Course updated successfully.");
      } else {
        await apiRequest("/courses/", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        setNotice("Course created successfully.");
      }

      resetForm();
      await loadCourses();
    } catch (err) {
      setError(err.message || "Unable to save course.");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (course) => {
    setEditingId(course.id);

    setForm({
      title: course.title ?? "",
      code: course.code ?? "",
      description: course.description ?? "",
      instructor: course.instructor ?? "",
      duration_weeks: String(course.duration_weeks ?? 12),
      is_active: course.is_active ?? true,
    });

    setErrors({});
    setError("");
    setNotice("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDelete = async (course) => {
    if (
      !window.confirm(
        `Are you sure you want to delete "${course.title}" (${course.code})?`
      )
    ) {
      return;
    }

    setError("");
    setNotice("");

    try {
      await apiRequest(`/courses/${course.id}`, {
        method: "DELETE",
      });

      if (editingId === course.id) resetForm();

      setNotice("Course deleted successfully.");
      await loadCourses();
    } catch (err) {
      setError(err.message || "Unable to delete course.");
    }
  };

  const filteredCourses = courses.filter((course) => {
    const matchesSearch = [
      course.title,
      course.code,
      course.description,
      course.instructor,
    ]
      .join(" ")
      .toLowerCase()
      .includes(search.trim().toLowerCase());

    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "active" && course.is_active) ||
      (statusFilter === "inactive" && !course.is_active);

    return matchesSearch && matchesStatus;
  });

  const activeCount = courses.filter((course) => course.is_active).length;

  return (
    <main className="page-container">
      <div className="students-heading">
        <div>
          <p className="eyebrow">COURSE DIRECTORY</p>
          <h1>Course Management</h1>
          <p>Create, update, search, and manage courses.</p>
        </div>

        <div className="course-summary">
          <div className="course-stat">
            <span>Total courses</span>
            <strong>{courses.length}</strong>
          </div>
          <div className="course-stat">
            <span>Active courses</span>
            <strong>{activeCount}</strong>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-message page-message" role="alert">
          {error}
        </div>
      )}

      {notice && (
        <div className="success-message page-message" role="status">
          {notice}
        </div>
      )}

      <section className="student-form-card">
        <h2>{editingId !== null ? "Edit course" : "Add a course"}</h2>
        <p>Enter the course details below.</p>

        <form onSubmit={handleSubmit} noValidate>
          <div className="student-form-grid">
            <div className="form-field">
              <label htmlFor="title">Course title</label>
              <input
                id="title"
                name="title"
                value={form.title}
                onChange={handleChange}
                minLength={2}
                maxLength={120}
                required
                aria-invalid={Boolean(errors.title)}
              />
              {errors.title && (
                <span className="field-error">{errors.title}</span>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="code">Course code</label>
              <input
                id="code"
                name="code"
                value={form.code}
                onChange={handleChange}
                minLength={2}
                maxLength={20}
                placeholder="e.g. PY101"
                required
                aria-invalid={Boolean(errors.code)}
              />
              {errors.code && (
                <span className="field-error">{errors.code}</span>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="instructor">Instructor</label>
              <input
                id="instructor"
                name="instructor"
                value={form.instructor}
                onChange={handleChange}
                minLength={2}
                maxLength={100}
                required
                aria-invalid={Boolean(errors.instructor)}
              />
              {errors.instructor && (
                <span className="field-error">{errors.instructor}</span>
              )}
            </div>

            <div className="form-field">
              <label htmlFor="duration_weeks">Duration (weeks)</label>
              <input
                id="duration_weeks"
                name="duration_weeks"
                type="number"
                min="1"
                max="520"
                step="1"
                value={form.duration_weeks}
                onChange={handleChange}
                required
                aria-invalid={Boolean(errors.duration_weeks)}
              />
              {errors.duration_weeks && (
                <span className="field-error">
                  {errors.duration_weeks}
                </span>
              )}
            </div>

            <div className="form-field full-width">
              <label htmlFor="description">Description (optional)</label>
              <textarea
                id="description"
                name="description"
                rows="4"
                maxLength={1000}
                value={form.description}
                onChange={handleChange}
                placeholder="Describe the course..."
              />
              <span className="character-count">
                {form.description.length}/1000 characters
              </span>
              {errors.description && (
                <span className="field-error">
                  {errors.description}
                </span>
              )}
            </div>

            {editingId !== null && (
              <div className="form-field full-width">
                <label className="checkbox-label" htmlFor="is_active">
                  <input
                    id="is_active"
                    name="is_active"
                    type="checkbox"
                    checked={form.is_active}
                    onChange={handleChange}
                  />
                  Course is active
                </label>
              </div>
            )}
          </div>

          <div className="form-actions">
            <button type="submit" disabled={saving}>
              {saving
                ? "Saving..."
                : editingId !== null
                  ? "Update course"
                  : "Add course"}
            </button>

            {editingId !== null && (
              <button
                type="button"
                className="secondary-button"
                onClick={resetForm}
                disabled={saving}
              >
                Cancel edit
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="student-list-section">
        <div className="student-list-heading">
          <div>
            <h2>Course records</h2>
            <p>Search courses or filter by active status.</p>
          </div>

          <div className="course-filters">
            <input
              className="student-search"
              type="search"
              placeholder="Search courses..."
              aria-label="Search courses"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />

            <select
              className="student-search"
              aria-label="Filter courses by status"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
            >
              <option value="all">All courses</option>
              <option value="active">Active only</option>
              <option value="inactive">Inactive only</option>
            </select>
          </div>
        </div>

        {loading ? (
          <p className="centered">Loading courses...</p>
        ) : filteredCourses.length === 0 ? (
          <div className="empty-state">
            <h3>No courses found</h3>
            <p>
              {search || statusFilter !== "all"
                ? "Try changing your search or filter."
                : "Add your first course using the form above."}
            </p>
          </div>
        ) : (
          <div className="student-table-wrapper">
            <table className="student-table">
              <thead>
                <tr>
                  <th>Course</th>
                  <th>Code</th>
                  <th>Instructor</th>
                  <th>Duration</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {filteredCourses.map((course) => (
                  <tr key={course.id}>
                    <td>
                      <strong>{course.title}</strong>
                      {course.description && (
                        <p className="course-description">
                          {course.description}
                        </p>
                      )}
                    </td>
                    <td>{course.code}</td>
                    <td>{course.instructor}</td>
                    <td>{course.duration_weeks} weeks</td>
                    <td>
                      <span
                        className={`status-badge ${
                          course.is_active ? "active-status" : "inactive-status"
                        }`}
                      >
                        {course.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td>
                      <div className="table-actions">
                        <button
                          type="button"
                          className="small-button"
                          onClick={() => handleEdit(course)}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          className="small-button danger-button"
                          onClick={() => handleDelete(course)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}

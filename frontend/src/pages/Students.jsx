
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";

const emptyForm = {
  name: "",
  email: "",
  phone: "",
  department: "",
  course: "",
};

function validateStudent(form) {
  const errors = {};

  for (const field of ["name", "department", "course"]) {
    const value = form[field].trim();

    if (value.length < 2 || !/[a-z]/i.test(value)) {
      errors[field] = "Enter at least 2 characters and include a letter.";
    } else if (!/^[\p{L}\s&.'-]+$/u.test(value)) {
      errors[field] = "Contains invalid characters.";
    }
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
    errors.email = "Enter a valid email address.";
  }

  const phone = form.phone.trim();

  if (
    !/^\+?[0-9][0-9 ()-]{8,18}[0-9]$/.test(phone) ||
    (phone.match(/[0-9]/g) || []).length < 10
  ) {
    errors.phone = "Enter a valid phone number with at least 10 digits.";
  }

  return errors;
}

export default function Students() {
  const [students, setStudents] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [search, setSearch] = useState("");
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadStudents = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest("/students/");
      setStudents(Array.isArray(data) ? data : data.students || []);
    } catch (err) {
      setError(err.message || "Unable to load students.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStudents();
  }, [loadStudents]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((current) => ({ ...current, [name]: value }));
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

    const validationErrors = validateStudent(form);
    setErrors(validationErrors);
    setNotice("");
    setError("");

    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setSaving(true);

    const payload = Object.fromEntries(
      Object.entries(form).map(([key, value]) => [key, value.trim()])
    );

    try {
      if (editingId !== null) {
        await apiRequest(`/students/${editingId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        setNotice("Student updated successfully.");
      } else {
        await apiRequest("/students/", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        setNotice("Student created successfully.");
      }

      resetForm();
      await loadStudents();
    } catch (err) {
      setError(err.message || "Unable to save student.");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (student) => {
    setEditingId(student.id);
    setForm({
      name: student.name ?? "",
      email: student.email ?? "",
      phone: student.phone ?? "",
      department: student.department ?? "",
      course: student.course ?? "",
    });
    setErrors({});
    setError("");
    setNotice("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDelete = async (student) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete ${student.name}?`
    );

    if (!confirmed) return;

    setError("");
    setNotice("");

    try {
      await apiRequest(`/students/${student.id}`, {
        method: "DELETE",
      });

      setNotice("Student deleted successfully.");

      if (editingId === student.id) {
        resetForm();
      }

      await loadStudents();
    } catch (err) {
      setError(err.message || "Unable to delete student.");
    }
  };

  const filteredStudents = students.filter((student) =>
    [
      student.name,
      student.email,
      student.phone,
      student.department,
      student.course,
    ]
      .join(" ")
      .toLowerCase()
      .includes(search.toLowerCase().trim())
  );

  return (
    <main className="page-container">
      <div className="students-heading">
        <div>
          <p className="eyebrow">STUDENT DIRECTORY</p>
          <h1>Student Management</h1>
          <p>Create, view, update, and delete student records.</p>
        </div>

        <div className="student-count">
          <span>Total students</span>
          <strong>{students.length}</strong>
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
        <h2>{editingId !== null ? "Edit student" : "Add a student"}</h2>
        <p>Complete all five fields below.</p>

        <form onSubmit={handleSubmit} noValidate>
          <div className="student-form-grid">
            {[
              { name: "name", label: "Full name", type: "text" },
              { name: "email", label: "Email address", type: "email" },
              { name: "phone", label: "Phone number", type: "tel" },
              { name: "department", label: "Department", type: "text" },
              { name: "course", label: "Course", type: "text" },
            ].map((field) => (
              <div className="form-field" key={field.name}>
                <label htmlFor={field.name}>{field.label}</label>
                <input
                  id={field.name}
                  name={field.name}
                  type={field.type}
                  value={form[field.name]}
                  onChange={handleChange}
                  maxLength={
                    field.name === "phone"
                      ? 20
                      : field.name === "email"
                        ? 254
                        : 100
                  }
                  required
                  aria-invalid={Boolean(errors[field.name])}
                  aria-describedby={
                    errors[field.name] ? `${field.name}-error` : undefined
                  }
                />
                {errors[field.name] && (
                  <span
                    className="field-error"
                    id={`${field.name}-error`}
                  >
                    {errors[field.name]}
                  </span>
                )}
              </div>
            ))}
          </div>

          <div className="form-actions">
            <button type="submit" disabled={saving}>
              {saving
                ? "Saving..."
                : editingId !== null
                  ? "Update student"
                  : "Add student"}
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
            <h2>Student records</h2>
            <p>Search by name, email, phone, department, or course.</p>
          </div>

          <input
            className="student-search"
            type="search"
            aria-label="Search students"
            placeholder="Search students..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        {loading ? (
          <p className="centered">Loading students...</p>
        ) : filteredStudents.length === 0 ? (
          <div className="empty-state">
            <h3>No students found</h3>
            <p>
              {search
                ? "Try another search term."
                : "Add your first student using the form above."}
            </p>
          </div>
        ) : (
          <div className="student-table-wrapper">
            <table className="student-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Department</th>
                  <th>Course</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredStudents.map((student) => (
                  <tr key={student.id}>
                    <td>{student.name}</td>
                    <td>{student.email}</td>
                    <td>{student.phone}</td>
                    <td>{student.department}</td>
                    <td>{student.course}</td>
                    <td>
                      <div className="table-actions">
                        <button
                          type="button"
                          className="small-button"
                          onClick={() => handleEdit(student)}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          className="small-button danger-button"
                          onClick={() => handleDelete(student)}
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

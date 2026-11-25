import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router";
import { RefreshCw, ShieldCheck, UserPlus, Users } from "lucide-react";
import type { Merchant, RoleCode, StaffAccount } from "../../domain/models";
import { useServices } from "@/app/providers/services-provider";
import { useSession } from "@/app/providers/session-provider";
import { getErrorMessage } from "@/shared/domain/app-error";
import { Button } from "@/shared/ui/button";
import { Field, PasswordField } from "@/shared/ui/field";
import { ManagerRestaurantsPanel } from "../components/manager-restaurants-panel";
import { ResourceState } from "../components/resource-state";
import { useResource } from "../hooks/use-resource";
import {
  hasAdminRole,
  hasCourierRole,
  hasKitchenRole,
  hasManagerRole,
  roleLabels,
} from "../status-labels";

const STAFF_ROLE_CHOICES: RoleCode[] = [
  "admin",
  "operations_manager",
  "restaurant_manager",
  "order_preparer",
  "courier",
];

const ALL_ROLE_CHOICES: RoleCode[] = [...STAFF_ROLE_CHOICES, "customer"];

const roleFilters: [string, string][] = [
  ["", "الكل"],
  ["admin", "الأدمن"],
  ["operations_manager", "مدير عمليات"],
  ["restaurant_manager", "مدير مطعم"],
  ["order_preparer", "محضّر طلبات"],
  ["courier", "مندوب توصيل"],
  ["customer", "عميل"],
];

function toggleRole(list: RoleCode[], role: RoleCode): RoleCode[] {
  if (list.includes(role)) {
    return list.length > 1 ? list.filter((item) => item !== role) : list;
  }
  return [...list, role];
}

function AdminUserCard({
  account,
  restaurants,
  currentAdminId,
  onUpdated,
}: {
  account: StaffAccount;
  restaurants: Merchant[];
  currentAdminId: string;
  onUpdated(): void;
}) {
  const { marketplace: services } = useServices();
  const [roles, setRoles] = useState<RoleCode[]>(
    account.roles as RoleCode[],
  );
  const [restaurantId, setRestaurantId] = useState(
    account.managedRestaurantIds[0] ?? "",
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");

  useEffect(() => {
    setRoles(account.roles as RoleCode[]);
    setRestaurantId(account.managedRestaurantIds[0] ?? "");
  }, [account.id, account.roles, account.managedRestaurantIds]);

  const needsRestaurant = roles.some((r) =>
    ["restaurant_manager", "order_preparer"].includes(r),
  );
  const isSelf = account.id === currentAdminId;

  async function save(nextIsActive?: boolean, nextEmailVerified?: boolean) {
    if (busy) return;
    setBusy(true);
    setError("");
    setSaved("");
    try {
      await services.operations.updateUserRoles(account.id, {
        roles,
        isActive: nextIsActive,
        emailVerified: nextEmailVerified,
        restaurantId: needsRestaurant && restaurantId ? restaurantId : undefined,
      });
      setSaved("تم حفظ التعديلات بنجاح.");
      onUpdated();
    } catch (cause) {
      setError(getErrorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="mp-admin-user-card">
      <div className="mp-section-title">
        <div>
          <h3>{account.name}</h3>
          <p className="mp-muted">
            <bdi dir="ltr">{account.email}</bdi>
            {account.phone ? (
              <>
                {" · "}
                <bdi dir="ltr">{account.phone}</bdi>
              </>
            ) : null}
          </p>
        </div>
        <div className="mp-inline-actions">
          {!account.emailVerified ? (
            <span className="mp-status is-pending">بريد غير مؤكد</span>
          ) : null}
          <span className={account.isActive ? "mp-status is-accepted" : "mp-status is-rejected"}>
            {account.isActive ? "نشط" : "موقوف"}
          </span>
        </div>
      </div>

      <div className="mp-role-checks" role="group" aria-label={`أدوار ${account.name}`}>
        {ALL_ROLE_CHOICES.map((role) => (
          <label key={role} className="mp-role-check">
            <input
              type="checkbox"
              checked={roles.includes(role)}
              disabled={busy}
              onChange={() => setRoles((old) => toggleRole(old, role))}
            />
            <span>{roleLabels[role] ?? role}</span>
          </label>
        ))}
      </div>

      {needsRestaurant ? (
        <label className="mp-store-select mp-admin-rest-select">
          <span>المطعم المرتبط</span>
          <select
            value={restaurantId}
            onChange={(e) => setRestaurantId(e.target.value)}
            disabled={busy}
          >
            <option value="">بدون ربط إضافي</option>
            {restaurants.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </label>
      ) : null}

      <div className="mp-inline-actions">
        <Button loading={busy} onClick={() => void save(account.isActive)}>
          حفظ الأدوار
        </Button>
        {!account.emailVerified ? (
          <Button
            variant="secondary"
            loading={busy}
            onClick={() => void save(account.isActive, true)}
          >
            تأكيد البريد يدويًا
          </Button>
        ) : null}
        {!isSelf ? (
          <Button
            variant="secondary"
            loading={busy}
            onClick={() => void save(!account.isActive)}
          >
            {account.isActive ? "إيقاف الحساب" : "إعادة تفعيل الحساب"}
          </Button>
        ) : null}
      </div>

      {saved ? (
        <p className="mp-success-banner" role="status">
          {saved}
        </p>
      ) : null}
      {error ? (
        <p className="mp-error" role="alert">
          {error}
        </p>
      ) : null}
    </article>
  );
}

export function AdminPage() {
  const { marketplace: services } = useServices();
  const { user } = useSession();
  const [tab, setTab] = useState<"staff" | "catalog">("staff");
  const [roleFilter, setRoleFilter] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [selectedRest, setSelectedRest] = useState("");

  // Create Staff state
  const [staffName, setStaffName] = useState("");
  const [staffEmail, setStaffEmail] = useState("");
  const [staffPhone, setStaffPhone] = useState("");
  const [staffPassword, setStaffPassword] = useState("");
  const [staffRoles, setStaffRoles] = useState<RoleCode[]>(["courier"]);
  const [staffRestaurantId, setStaffRestaurantId] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [createSuccess, setCreateSuccess] = useState("");

  const isAdmin = hasAdminRole(user?.roles);

  const restaurants = useResource(
    useCallback(
      (signal: AbortSignal) =>
        isAdmin
          ? services.operations.listManagedRestaurants(signal)
          : Promise.resolve([]),
      [services, isAdmin, user?.id],
    ),
  );

  const directory = useResource(
    useCallback(
      (signal: AbortSignal) =>
        isAdmin
          ? services.operations.listUsers(
              {
                role: roleFilter || undefined,
                search: appliedSearch || undefined,
                limit: 20,
                offset,
              },
              signal,
            )
          : Promise.resolve({ items: [], hasMore: false }),
      [services, isAdmin, roleFilter, appliedSearch, offset, user?.id],
    ),
  );

  if (!isAdmin) {
    return (
      <div className="mp-resource">
        <h1>غير مصرح بالدخول</h1>
        <p>بوابة الأدمن متاحة لمديري المنصة فقط.</p>
        {hasManagerRole(user?.roles) ? (
          <Link className="button button-primary" to="/operations">
            الانتقال إلى بوابة المدير
          </Link>
        ) : hasKitchenRole(user?.roles) ? (
          <Link className="button button-primary" to="/kitchen">
            الانتقال إلى بوابة تحضير الطلبات
          </Link>
        ) : hasCourierRole(user?.roles) ? (
          <Link className="button button-primary" to="/delivery">
            الانتقال إلى بوابة المندوب
          </Link>
        ) : (
          <Link className="button button-primary" to="/">
            العودة إلى المتجر
          </Link>
        )}
      </div>
    );
  }

  const activeRestId = restaurants.data?.some((r) => r.id === selectedRest)
    ? selectedRest
    : (restaurants.data?.[0]?.id ?? "");
  const showStaffRestaurant = staffRoles.some((r) =>
    ["restaurant_manager", "order_preparer"].includes(r),
  );

  async function handleCreateStaff(e: React.FormEvent) {
    e.preventDefault();
    if (creating) return;
    setCreating(true);
    setCreateError("");
    setCreateSuccess("");
    try {
      const created = await services.operations.createStaff({
        name: staffName.trim(),
        email: staffEmail.trim(),
        password: staffPassword,
        phone: staffPhone.trim() || null,
        roles: staffRoles,
        restaurantId:
          showStaffRestaurant && staffRestaurantId ? staffRestaurantId : null,
      });
      setCreateSuccess(
        `تم إنشاء حساب "${created.name}" (${created.email}) وتفعيله فورًا بدون انتظار بريد تأكيد.`,
      );
      setStaffName("");
      setStaffEmail("");
      setStaffPhone("");
      setStaffPassword("");
      directory.reload();
    } catch (cause) {
      setCreateError(getErrorMessage(cause));
    } finally {
      setCreating(false);
    }
  }

  return (
    <>
      <div className="mp-page-heading">
        <ShieldCheck aria-hidden="true" />
        <h1 tabIndex={-1}>بوابة الأدمن — إدارة المنصة والطاقم</h1>
        <p>
          إنشاء حسابات المناديب والمحضّرين ومديري المطاعم وتعيين الأدوار، وإدارة مطاعم المنصة بالكامل.
        </p>
      </div>

      <div className="mp-portal-tabs" role="tablist" aria-label="أقسام بوابة الأدمن">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "staff"}
          className={tab === "staff" ? "mp-tab-btn active" : "mp-tab-btn"}
          onClick={() => setTab("staff")}
        >
          إدارة الحسابات والطاقم والأدوار
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "catalog"}
          className={tab === "catalog" ? "mp-tab-btn active" : "mp-tab-btn"}
          onClick={() => setTab("catalog")}
        >
          إدارة المطاعم والمنيو
        </button>
      </div>

      {tab === "catalog" ? (
        <ManagerRestaurantsPanel
          restaurants={restaurants.data ?? []}
          selectedId={activeRestId}
          isGlobalOperator={true}
          onSelectRestaurant={setSelectedRest}
          onRestaurantsChanged={(newId) => {
            if (newId) setSelectedRest(newId);
            restaurants.reload();
          }}
        />
      ) : (
        <div className="mp-admin-workspace">
          <section className="mp-portal-card">
            <h2>
              <UserPlus aria-hidden="true" size={20} />
              إنشاء حساب موظف جديد (مفعّل فورًا)
            </h2>
            {createSuccess ? (
              <p className="mp-success-banner" role="status">
                {createSuccess}
              </p>
            ) : null}
            {createError ? (
              <p className="mp-error" role="alert">
                {createError}
              </p>
            ) : null}
            <form className="mp-manager-form" onSubmit={(e) => void handleCreateStaff(e)}>
              <div className="mp-three-col">
                <Field
                  label="الاسم الكامل"
                  value={staffName}
                  onChange={(e) => setStaffName(e.target.value)}
                  required
                  minLength={2}
                  maxLength={100}
                  placeholder="مثال: محمود المندوب"
                />
                <Field
                  label="البريد الإلكتروني"
                  type="email"
                  value={staffEmail}
                  onChange={(e) => setStaffEmail(e.target.value)}
                  required
                  dir="ltr"
                  placeholder="staff@foodify.example.com"
                />
                <Field
                  label="رقم الهاتف (اختياري)"
                  value={staffPhone}
                  onChange={(e) => setStaffPhone(e.target.value)}
                  dir="ltr"
                  placeholder="+201012345678"
                />
              </div>

              <PasswordField
                label="كلمة المرور المبدئية"
                value={staffPassword}
                onChange={(e) => setStaffPassword(e.target.value)}
                required
                minLength={15}
                maxLength={128}
                hint="15 حرف على الأقل حسب سياسة أمان النظام."
              />

              <div className="mp-role-checks" role="group" aria-label="اختر أدوار الموظف">
                {STAFF_ROLE_CHOICES.map((role) => (
                  <label key={role} className="mp-role-check">
                    <input
                      type="checkbox"
                      checked={staffRoles.includes(role)}
                      disabled={creating}
                      onChange={() =>
                        setStaffRoles((old) => toggleRole(old, role))
                      }
                    />
                    <span>{roleLabels[role] ?? role}</span>
                  </label>
                ))}
              </div>

              {showStaffRestaurant ? (
                <label className="mp-store-select mp-admin-rest-select">
                  <span>ربط مباشر بمطعم (اختياري)</span>
                  <select
                    value={staffRestaurantId}
                    onChange={(e) => setStaffRestaurantId(e.target.value)}
                  >
                    <option value="">بدون ربط مبدئي</option>
                    {(restaurants.data ?? []).map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}

              <Button type="submit" loading={creating}>
                إنشاء حساب الموظف وتفعيله
              </Button>
            </form>
          </section>

          <section className="mp-portal-card">
            <div className="mp-manager-controls">
              <h2>
                <Users aria-hidden="true" size={20} />
                دليل المستخدمين وتعديل الأدوار
              </h2>
              <button
                type="button"
                className="button button-secondary mp-refresh-btn"
                onClick={directory.reload}
              >
                <RefreshCw aria-hidden="true" size={16} />
                تحديث الدليل
              </button>
            </div>

            <form
              className="mp-admin-search"
              onSubmit={(e) => {
                e.preventDefault();
                setAppliedSearch(searchInput.trim());
                setOffset(0);
              }}
            >
              <Field
                label="بحث بالاسم أو البريد"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="اكتب اسمًا أو بريدًا إلكترونيًا..."
              />
              <Button type="submit" variant="secondary">
                بحث
              </Button>
            </form>

            <div className="mp-filter-pills" role="group" aria-label="تصفية حسب الدور">
              {roleFilters.map(([code, label]) => (
                <button
                  key={code || "all"}
                  type="button"
                  className={
                    roleFilter === code ? "mp-pill-tab active" : "mp-pill-tab"
                  }
                  aria-pressed={roleFilter === code}
                  onClick={() => {
                    setRoleFilter(code);
                    setOffset(0);
                  }}
                >
                  {label}
                </button>
              ))}
            </div>

            {directory.loading || directory.error ? (
              <ResourceState
                loading={directory.loading}
                error={directory.error}
                retry={directory.reload}
              />
            ) : directory.data?.items.length ? (
              <div className="mp-admin-users-grid">
                {directory.data.items.map((account) => (
                  <AdminUserCard
                    key={account.id}
                    account={account}
                    restaurants={restaurants.data ?? []}
                    currentAdminId={user?.id ?? ""}
                    onUpdated={directory.reload}
                  />
                ))}
              </div>
            ) : (
              <ResourceState error="لا يوجد مستخدمون مطابقون للبحث." />
            )}

            <div className="mp-pagination">
              {offset > 0 ? (
                <button
                  type="button"
                  onClick={() => setOffset((v) => Math.max(0, v - 20))}
                >
                  السابق
                </button>
              ) : null}
              {directory.data?.hasMore ? (
                <button
                  type="button"
                  onClick={() => setOffset((v) => v + 20)}
                >
                  التالي
                </button>
              ) : null}
            </div>
          </section>
        </div>
      )}
    </>
  );
}

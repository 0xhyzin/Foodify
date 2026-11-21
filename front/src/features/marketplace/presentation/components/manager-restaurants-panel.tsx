import { useCallback, useEffect, useState } from "react";
import { PlusCircle, Store, UserPlus, UtensilsCrossed } from "lucide-react";
import type { Merchant, MerchantKind, Product } from "../../domain/models";
import { formatMoney } from "../../domain/money";
import { useServices } from "@/app/providers/services-provider";
import { getErrorMessage } from "@/shared/domain/app-error";
import { Button } from "@/shared/ui/button";
import { Field } from "@/shared/ui/field";
import { useResource } from "../hooks/use-resource";
import { ResourceState } from "./resource-state";

export function ManagerRestaurantsPanel({
  restaurants,
  selectedId,
  isGlobalOperator,
  onSelectRestaurant,
  onRestaurantsChanged,
}: {
  restaurants: Merchant[];
  selectedId: string;
  isGlobalOperator: boolean;
  onSelectRestaurant(id: string): void;
  onRestaurantsChanged(selectId?: string): void;
}) {
  const { marketplace: services } = useServices();
  const selectedRestaurant =
    restaurants.find((r) => r.id === selectedId) ?? null;

  const [busy, setBusy] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState("");

  // Create Restaurant state
  const [newName, setNewName] = useState("");
  const [newCategory, setNewCategory] = useState("");
  const [newKind, setNewKind] = useState<MerchantKind>("restaurant");
  const [newAddress, setNewAddress] = useState("");
  const [newFee, setNewFee] = useState("15.00");
  const [newMinutes, setNewMinutes] = useState("35");
  const [newDesc, setNewDesc] = useState("");

  // Edit Restaurant state
  const [editName, setEditName] = useState("");
  const [editCategory, setEditCategory] = useState("");
  const [editKind, setEditKind] = useState<MerchantKind>("restaurant");
  const [editAddress, setEditAddress] = useState("");
  const [editFee, setEditFee] = useState("0.00");
  const [editMinutes, setEditMinutes] = useState("35");
  const [editDesc, setEditDesc] = useState("");

  // Assign Staff state
  const [staffUserId, setStaffUserId] = useState("");

  // Add Menu Item state
  const [itemName, setItemName] = useState("");
  const [itemCategory, setItemCategory] = useState("");
  const [itemPrice, setItemPrice] = useState("");
  const [itemDesc, setItemDesc] = useState("");

  useEffect(() => {
    if (!selectedRestaurant) return;
    setEditName(selectedRestaurant.name);
    setEditCategory(selectedRestaurant.category);
    setEditKind(selectedRestaurant.kind);
    setEditAddress(selectedRestaurant.address ?? "");
    setEditFee(selectedRestaurant.deliveryFee);
    setEditMinutes(String(selectedRestaurant.minutes));
    setEditDesc(selectedRestaurant.description);
  }, [selectedRestaurant]);

  const menu = useResource(
    useCallback(
      (signal: AbortSignal) =>
        selectedId
          ? services.catalog.menu(selectedId, signal)
          : Promise.resolve([] as Product[]),
      [services, selectedId],
    ),
  );

  async function runAction(message: string, action: () => Promise<unknown>) {
    if (busy) return;
    setBusy(true);
    setError("");
    setStatusMessage("");
    try {
      await action();
      setStatusMessage(message);
    } catch (cause) {
      setError(getErrorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mp-manager-catalog">
      {statusMessage ? (
        <p className="mp-success-banner" role="status">
          {statusMessage}
        </p>
      ) : null}
      {error ? (
        <p className="mp-error" role="alert">
          {error}
        </p>
      ) : null}

      <div className="mp-manager-catalog-grid">
        {isGlobalOperator ? (
          <section className="mp-portal-card">
            <h2>
              <PlusCircle aria-hidden="true" size={20} />
              إضافة مطعم / متجر جديد
            </h2>
            <form
              className="mp-manager-form"
              onSubmit={(e) => {
                e.preventDefault();
                void runAction("تم إضافة المطعم بنجاح.", async () => {
                  const created = await services.operations.createRestaurant({
                    name: newName.trim(),
                    category: newCategory.trim(),
                    kind: newKind,
                    address: newAddress.trim(),
                    deliveryFee: newFee.trim() || "0.00",
                    deliveryMinutes: Number(newMinutes) || 35,
                    description: newDesc.trim() || undefined,
                  });
                  setNewName("");
                  setNewCategory("");
                  setNewAddress("");
                  setNewDesc("");
                  onRestaurantsChanged(created.id);
                });
              }}
            >
              <Field
                label="اسم المطعم"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                required
                minLength={2}
                maxLength={160}
                placeholder="مثال: مشويات بورسعيد"
              />
              <div className="mp-two-col">
                <Field
                  label="التصنيف"
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  required
                  minLength={2}
                  maxLength={80}
                  placeholder="مثال: مشويات / مأكولات بحرية"
                />
                <label className="field">
                  <span className="label-row">
                    <span>النوع</span>
                  </span>
                  <select
                    value={newKind}
                    onChange={(e) => setNewKind(e.target.value as MerchantKind)}
                  >
                    <option value="restaurant">مطعم</option>
                    <option value="dessert">حلويات وقهوة</option>
                    <option value="grocery">بقالة</option>
                  </select>
                </label>
              </div>
              <Field
                label="عنوان الفرع"
                value={newAddress}
                onChange={(e) => setNewAddress(e.target.value)}
                required
                minLength={3}
                maxLength={300}
                placeholder="مثال: شارع الجمهورية، حي الشرق، بورسعيد"
              />
              <div className="mp-two-col">
                <Field
                  label="رسوم التوصيل (ج.م)"
                  type="number"
                  step="0.50"
                  min="0"
                  max="5000"
                  value={newFee}
                  onChange={(e) => setNewFee(e.target.value)}
                  required
                  dir="ltr"
                />
                <Field
                  label="وقت التوصيل المتوقع (دقيقة)"
                  type="number"
                  min="5"
                  max="180"
                  value={newMinutes}
                  onChange={(e) => setNewMinutes(e.target.value)}
                  required
                  dir="ltr"
                />
              </div>
              <Field
                label="وصف مختصر (اختياري)"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                maxLength={1000}
              />
              <Button type="submit" loading={busy}>
                إضافة المطعم
              </Button>
            </form>
          </section>
        ) : null}

        <section className="mp-portal-card">
          <h2>
            <Store aria-hidden="true" size={20} />
            إدارة المطعم المحدد
          </h2>
          {restaurants.length ? (
            <>
              <label className="mp-store-select">
                <span>اختر المطعم</span>
                <select
                  value={selectedId}
                  onChange={(e) => onSelectRestaurant(e.target.value)}
                >
                  {restaurants.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </label>

              {selectedRestaurant ? (
                <form
                  className="mp-manager-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void runAction("تم تحديث بيانات المطعم.", async () => {
                      await services.operations.updateRestaurant(
                        selectedRestaurant.id,
                        {
                          name: editName.trim(),
                          category: editCategory.trim(),
                          kind: editKind,
                          address: editAddress.trim(),
                          deliveryFee: editFee.trim() || "0.00",
                          deliveryMinutes: Number(editMinutes) || 35,
                          description: editDesc.trim() || null,
                        },
                      );
                      onRestaurantsChanged(selectedRestaurant.id);
                    });
                  }}
                >
                  <Field
                    label="اسم المطعم"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    required
                    minLength={2}
                    maxLength={160}
                  />
                  <div className="mp-two-col">
                    <Field
                      label="التصنيف"
                      value={editCategory}
                      onChange={(e) => setEditCategory(e.target.value)}
                      required
                      minLength={2}
                      maxLength={80}
                    />
                    <label className="field">
                      <span className="label-row">
                        <span>النوع</span>
                      </span>
                      <select
                        value={editKind}
                        onChange={(e) =>
                          setEditKind(e.target.value as MerchantKind)
                        }
                      >
                        <option value="restaurant">مطعم</option>
                        <option value="dessert">حلويات وقهوة</option>
                        <option value="grocery">بقالة</option>
                      </select>
                    </label>
                  </div>
                  <Field
                    label="عنوان الفرع"
                    value={editAddress}
                    onChange={(e) => setEditAddress(e.target.value)}
                    required
                    minLength={3}
                    maxLength={300}
                  />
                  <div className="mp-two-col">
                    <Field
                      label="رسوم التوصيل (ج.م)"
                      type="number"
                      step="0.50"
                      min="0"
                      max="5000"
                      value={editFee}
                      onChange={(e) => setEditFee(e.target.value)}
                      required
                      dir="ltr"
                    />
                    <Field
                      label="وقت التوصيل (دقيقة)"
                      type="number"
                      min="5"
                      max="180"
                      value={editMinutes}
                      onChange={(e) => setEditMinutes(e.target.value)}
                      required
                      dir="ltr"
                    />
                  </div>
                  <Field
                    label="الوصف"
                    value={editDesc}
                    onChange={(e) => setEditDesc(e.target.value)}
                    maxLength={1000}
                  />
                  <div className="mp-inline-actions">
                    <Button type="submit" loading={busy}>
                      حفظ بيانات المطعم
                    </Button>
                    <Button
                      variant="secondary"
                      loading={busy}
                      onClick={() =>
                        void runAction("تم إيقاف المطعم مؤقتًا.", async () => {
                          await services.operations.updateRestaurant(
                            selectedRestaurant.id,
                            { isActive: false },
                          );
                          onRestaurantsChanged();
                        })
                      }
                    >
                      إيقاف مؤقت
                    </Button>
                    <Button
                      variant="secondary"
                      loading={busy}
                      onClick={() =>
                        void runAction("تم تفعيل المطعم.", async () => {
                          await services.operations.updateRestaurant(
                            selectedRestaurant.id,
                            { isActive: true },
                          );
                          onRestaurantsChanged(selectedRestaurant.id);
                        })
                      }
                    >
                      تفعيل
                    </Button>
                  </div>
                </form>
              ) : null}

              {isGlobalOperator && selectedRestaurant ? (
                <form
                  className="mp-manager-subform"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void runAction("تم ربط الموظف بالمطعم.", async () => {
                      await services.operations.assignStaff(
                        selectedRestaurant.id,
                        staffUserId.trim(),
                      );
                      setStaffUserId("");
                    });
                  }}
                >
                  <h3>
                    <UserPlus aria-hidden="true" size={17} />
                    ربط مدير مطعم أو محضّر طلبات بالمطعم
                  </h3>
                  <div className="mp-inline-actions">
                    <Field
                      label="معرّف الموظف (User UUID)"
                      value={staffUserId}
                      onChange={(e) => setStaffUserId(e.target.value)}
                      required
                      dir="ltr"
                      placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                    />
                    <Button type="submit" variant="secondary" loading={busy}>
                      ربط بالمطعم
                    </Button>
                  </div>
                </form>
              ) : null}
            </>
          ) : (
            <p>مفيش مطاعم محددة حاليًا.</p>
          )}
        </section>
      </div>

      {selectedRestaurant ? (
        <section className="mp-portal-card mp-menu-manager-card">
          <h2>
            <UtensilsCrossed aria-hidden="true" size={20} />
            منيو {selectedRestaurant.name}
          </h2>

          <form
            className="mp-manager-form mp-menu-create-form"
            onSubmit={(e) => {
              e.preventDefault();
              void runAction("تم إضافة الصنف للمنيو.", async () => {
                await services.operations.createMenuItem(
                  selectedRestaurant.id,
                  {
                    name: itemName.trim(),
                    category: itemCategory.trim(),
                    price: itemPrice.trim(),
                    description: itemDesc.trim() || undefined,
                  },
                );
                setItemName("");
                setItemCategory("");
                setItemPrice("");
                setItemDesc("");
                menu.reload();
              });
            }}
          >
            <div className="mp-three-col">
              <Field
                label="اسم الصنف"
                value={itemName}
                onChange={(e) => setItemName(e.target.value)}
                required
                minLength={2}
                maxLength={160}
                placeholder="مثال: وجبة كباب"
              />
              <Field
                label="القسم"
                value={itemCategory}
                onChange={(e) => setItemCategory(e.target.value)}
                required
                minLength={2}
                maxLength={100}
                placeholder="مثال: الأطباق الرئيسية"
              />
              <Field
                label="السعر (ج.م)"
                type="number"
                step="0.50"
                min="0"
                max="50000"
                value={itemPrice}
                onChange={(e) => setItemPrice(e.target.value)}
                required
                dir="ltr"
              />
            </div>
            <Field
              label="وصف الصنف (اختياري)"
              value={itemDesc}
              onChange={(e) => setItemDesc(e.target.value)}
              maxLength={1000}
            />
            <Button type="submit" loading={busy}>
              إضافة صنف للمنيو
            </Button>
          </form>

          {menu.loading || menu.error ? (
            <ResourceState
              loading={menu.loading}
              error={menu.error}
              retry={menu.reload}
            />
          ) : menu.data?.length ? (
            <ul className="mp-manager-menu-list">
              {menu.data.map((item) => (
                <li key={item.id} className="mp-manager-menu-row">
                  <div>
                    <strong>{item.name}</strong>
                    <span>
                      {item.category} · {formatMoney(item.price)}
                    </span>
                  </div>
                  <Button
                    variant={item.available ? "secondary" : "primary"}
                    loading={busy}
                    onClick={() =>
                      void runAction(
                        item.available
                          ? `تم إيقاف "${item.name}".`
                          : `تم تفعيل "${item.name}".`,
                        async () => {
                          await services.operations.updateMenuItem(
                            selectedRestaurant.id,
                            item.id,
                            { isAvailable: !item.available },
                          );
                          menu.reload();
                        },
                      )
                    }
                  >
                    {item.available ? "متاح — إيقاف مؤقت" : "غير متاح — تفعيل"}
                  </Button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mp-muted">مفيش أصناف مضافة في المنيو ده لسه.</p>
          )}
        </section>
      ) : null}
    </div>
  );
}

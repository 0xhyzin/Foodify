-- مخطط MySQL الناتج عن Alembic حتى migration 20261031_0005.
-- أُنتج في الوضع offline؛ لم يُنفذ على قاعدة بيانات.
-- على قاعدة قائمة استخدم alembic upgrade head بدل إعادة تشغيل ملف bootstrap.
-- تُنفذ بيانات الأدوار وكتالوج المطاعم بأوامر seed منفصلة.

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 20261020_0001

CREATE TABLE roles (
    id INTEGER NOT NULL AUTO_INCREMENT,
    code VARCHAR(40) NOT NULL,
    name VARCHAR(100) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_roles_code UNIQUE (code)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE permissions (
    id INTEGER NOT NULL AUTO_INCREMENT,
    code VARCHAR(80) NOT NULL,
    name VARCHAR(150) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_permissions_code UNIQUE (code)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE token_types (
    id INTEGER NOT NULL AUTO_INCREMENT,
    code VARCHAR(40) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_token_types_code UNIQUE (code)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE users (
    id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(254) COLLATE utf8mb4_bin NOT NULL,
    phone VARCHAR(16),
    password_hash VARCHAR(255),
    is_email_verified BOOL NOT NULL,
    is_active BOOL NOT NULL,
    default_address_id VARCHAR(36),
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_users_email UNIQUE (email)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE user_roles (
    user_id VARCHAR(36) NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    CONSTRAINT fk_user_roles_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_role FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    CONSTRAINT fk_role_permissions_role FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE,
    CONSTRAINT fk_role_permissions_permission FOREIGN KEY(permission_id) REFERENCES permissions (id) ON DELETE CASCADE
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE addresses (
    id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    label VARCHAR(50) NOT NULL,
    recipient_name VARCHAR(100) NOT NULL,
    phone VARCHAR(16) NOT NULL,
    country_code VARCHAR(2) NOT NULL,
    city VARCHAR(100) NOT NULL,
    area VARCHAR(100) NOT NULL,
    street VARCHAR(200) NOT NULL,
    building VARCHAR(50) NOT NULL,
    floor VARCHAR(30),
    apartment VARCHAR(30),
    delivery_notes VARCHAR(500),
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_address_latitude CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    CONSTRAINT ck_address_longitude CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180),
    CONSTRAINT ck_address_coordinates CHECK ((latitude IS NULL AND longitude IS NULL) OR (latitude IS NOT NULL AND longitude IS NOT NULL)),
    CONSTRAINT fk_addresses_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE INDEX ix_addresses_user_created ON addresses (user_id, created_at);

CREATE TABLE auth_sessions (
    id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    created_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    revoked_at DATETIME,
    PRIMARY KEY (id),
    CONSTRAINT fk_auth_sessions_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE INDEX ix_auth_sessions_user_expires ON auth_sessions (user_id, expires_at);

CREATE TABLE refresh_tokens (
    id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    created_at DATETIME NOT NULL,
    used_at DATETIME,
    PRIMARY KEY (id),
    CONSTRAINT fk_refresh_tokens_session FOREIGN KEY(session_id) REFERENCES auth_sessions (id) ON DELETE CASCADE,
    CONSTRAINT uq_refresh_tokens_hash UNIQUE (token_hash)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE INDEX ix_refresh_tokens_session ON refresh_tokens (session_id);

CREATE TABLE action_tokens (
    id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    token_type_id INTEGER NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    expires_at DATETIME NOT NULL,
    consumed_at DATETIME,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_action_tokens_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_action_tokens_type FOREIGN KEY(token_type_id) REFERENCES token_types (id) ON DELETE RESTRICT,
    CONSTRAINT uq_action_tokens_hash UNIQUE (token_hash)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE INDEX ix_action_tokens_user_type ON action_tokens (user_id, token_type_id);

CREATE TABLE social_accounts (
    id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    provider VARCHAR(20) NOT NULL,
    provider_subject VARCHAR(255) COLLATE utf8mb4_bin NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_social_accounts_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT uq_social_provider_subject UNIQUE (provider, provider_subject),
    CONSTRAINT uq_social_user_provider UNIQUE (user_id, provider)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE oauth_states (
    state_hash VARCHAR(64) NOT NULL,
    provider VARCHAR(20) NOT NULL,
    code_verifier VARCHAR(128) NOT NULL,
    nonce VARCHAR(128) NOT NULL,
    binding_hash VARCHAR(64) NOT NULL,
    expires_at DATETIME NOT NULL,
    consumed_at DATETIME,
    PRIMARY KEY (state_hash)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE INDEX ix_oauth_states_expires_at ON oauth_states (expires_at);

CREATE TABLE oauth_tickets (
    ticket_hash VARCHAR(64) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    binding_hash VARCHAR(64) NOT NULL,
    expires_at DATETIME NOT NULL,
    consumed_at DATETIME,
    PRIMARY KEY (ticket_hash),
    CONSTRAINT fk_oauth_tickets_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE INDEX ix_oauth_tickets_expires_at ON oauth_tickets (expires_at);

CREATE TABLE email_outbox (
    id VARCHAR(36) NOT NULL,
    encrypted_payload TEXT NOT NULL,
    attempts INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    next_attempt_at DATETIME NOT NULL,
    sent_at DATETIME,
    PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE INDEX ix_email_outbox_pending ON email_outbox (sent_at, next_attempt_at);

ALTER TABLE users ADD CONSTRAINT fk_users_default_address FOREIGN KEY(default_address_id) REFERENCES addresses (id) ON DELETE SET NULL;

INSERT INTO alembic_version (version_num) VALUES ('20261020_0001');

-- Running upgrade 20261020_0001 -> 20261030_0002

CREATE TABLE restaurants (
    id VARCHAR(36) NOT NULL,
    name VARCHAR(160) NOT NULL,
    category VARCHAR(80) NOT NULL,
    description TEXT,
    address VARCHAR(300) NOT NULL,
    image VARCHAR(500),
    rating NUMERIC(3, 2) NOT NULL DEFAULT '0',
    reviews INTEGER NOT NULL DEFAULT '0',
    delivery_minutes INTEGER NOT NULL DEFAULT '35',
    is_active BOOL NOT NULL DEFAULT true,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE INDEX ix_restaurants_name ON restaurants (name);

CREATE INDEX ix_restaurants_category ON restaurants (category);

CREATE INDEX ix_restaurants_is_active ON restaurants (is_active);

CREATE TABLE menu_items (
    id VARCHAR(36) NOT NULL,
    restaurant_id VARCHAR(36) NOT NULL,
    name VARCHAR(160) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    description TEXT,
    image VARCHAR(500),
    is_available BOOL NOT NULL DEFAULT true,
    PRIMARY KEY (id),
    CONSTRAINT ck_menu_item_price CHECK (price >= 0),
    FOREIGN KEY(restaurant_id) REFERENCES restaurants (id) ON DELETE CASCADE
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE INDEX ix_menu_items_restaurant_id ON menu_items (restaurant_id);

CREATE INDEX ix_menu_items_category ON menu_items (category);

CREATE INDEX ix_menu_items_is_available ON menu_items (is_available);

CREATE INDEX ix_menu_restaurant_category ON menu_items (restaurant_id, category);

CREATE TABLE carts (
    id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    restaurant_id VARCHAR(36),
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY(restaurant_id) REFERENCES restaurants (id) ON DELETE SET NULL
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE UNIQUE INDEX ix_carts_user_id ON carts (user_id);

CREATE TABLE cart_items (
    id VARCHAR(36) NOT NULL,
    cart_id VARCHAR(36) NOT NULL,
    menu_item_id VARCHAR(36) NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_cart_item_quantity CHECK (quantity > 0),
    CONSTRAINT uq_cart_menu_item UNIQUE (cart_id, menu_item_id),
    FOREIGN KEY(cart_id) REFERENCES carts (id) ON DELETE CASCADE,
    FOREIGN KEY(menu_item_id) REFERENCES menu_items (id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE INDEX ix_cart_items_cart_id ON cart_items (cart_id);

CREATE TABLE food_orders (
    id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    restaurant_id VARCHAR(36) NOT NULL,
    address_id VARCHAR(36) NOT NULL,
    status VARCHAR(30) NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    payment_status VARCHAR(30) NOT NULL,
    subtotal NUMERIC(10, 2) NOT NULL,
    delivery_fee NUMERIC(10, 2) NOT NULL,
    total NUMERIC(10, 2) NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY(restaurant_id) REFERENCES restaurants (id) ON DELETE RESTRICT,
    FOREIGN KEY(address_id) REFERENCES addresses (id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE INDEX ix_food_orders_user_id ON food_orders (user_id);

CREATE INDEX ix_food_orders_status ON food_orders (status);

CREATE INDEX ix_food_orders_user_created ON food_orders (user_id, created_at);

CREATE TABLE food_order_items (
    id VARCHAR(36) NOT NULL,
    order_id VARCHAR(36) NOT NULL,
    menu_item_id VARCHAR(36) NOT NULL,
    item_name VARCHAR(160) NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_order_item_quantity CHECK (quantity > 0),
    CONSTRAINT ck_order_item_price CHECK (unit_price >= 0),
    FOREIGN KEY(order_id) REFERENCES food_orders (id) ON DELETE CASCADE,
    FOREIGN KEY(menu_item_id) REFERENCES menu_items (id) ON DELETE RESTRICT
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE INDEX ix_food_order_items_order_id ON food_order_items (order_id);

CREATE TABLE payments (
    id VARCHAR(36) NOT NULL,
    order_id VARCHAR(36) NOT NULL,
    provider VARCHAR(30) NOT NULL,
    status VARCHAR(30) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    reference VARCHAR(80) NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (order_id),
    UNIQUE (reference),
    FOREIGN KEY(order_id) REFERENCES food_orders (id) ON DELETE CASCADE
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE UNIQUE INDEX ix_payments_order_id ON payments (order_id);

UPDATE alembic_version SET version_num='20261030_0002' WHERE alembic_version.version_num = '20261020_0001';

-- Running upgrade 20261030_0002 -> 20261030_0003

ALTER TABLE restaurants ADD COLUMN delivery_fee NUMERIC(10, 2) NOT NULL DEFAULT '0';

ALTER TABLE restaurants ADD CONSTRAINT ck_restaurant_rating CHECK (rating BETWEEN 0 AND 5);

ALTER TABLE restaurants ADD CONSTRAINT ck_restaurant_reviews CHECK (reviews >= 0);

ALTER TABLE restaurants ADD CONSTRAINT ck_restaurant_delivery_minutes CHECK (delivery_minutes >= 0);

ALTER TABLE restaurants ADD CONSTRAINT ck_restaurant_delivery_fee CHECK (delivery_fee >= 0);

ALTER TABLE cart_items ADD CONSTRAINT ck_cart_item_max_quantity CHECK (quantity <= 99);

ALTER TABLE food_order_items ADD CONSTRAINT ck_order_item_max_quantity CHECK (quantity <= 99);

ALTER TABLE food_orders ADD COLUMN delivery_address JSON;

UPDATE food_orders AS o JOIN addresses AS a ON a.id = o.address_id
        SET o.delivery_address = JSON_OBJECT(
            'label', a.label, 'recipient_name', a.recipient_name, 'phone', a.phone,
            'country_code', a.country_code, 'city', a.city, 'area', a.area,
            'street', a.street, 'building', a.building, 'floor', a.floor,
            'apartment', a.apartment, 'delivery_notes', a.delivery_notes,
            'latitude', a.latitude, 'longitude', a.longitude);

ALTER TABLE food_orders MODIFY delivery_address JSON NOT NULL;

SET @foodify_fk = (SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'food_orders' AND COLUMN_NAME = 'user_id' AND REFERENCED_TABLE_NAME IS NOT NULL LIMIT 1);

SET @foodify_ddl = CONCAT('ALTER TABLE `food_orders` DROP FOREIGN KEY `', @foodify_fk, '`');

PREPARE foodify_stmt FROM @foodify_ddl;

EXECUTE foodify_stmt;

DEALLOCATE PREPARE foodify_stmt;

ALTER TABLE food_orders ADD CONSTRAINT fk_food_orders_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT;

SET @foodify_fk = (SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'food_orders' AND COLUMN_NAME = 'address_id' AND REFERENCED_TABLE_NAME IS NOT NULL LIMIT 1);

SET @foodify_ddl = CONCAT('ALTER TABLE `food_orders` DROP FOREIGN KEY `', @foodify_fk, '`');

PREPARE foodify_stmt FROM @foodify_ddl;

EXECUTE foodify_stmt;

DEALLOCATE PREPARE foodify_stmt;

ALTER TABLE food_orders MODIFY address_id VARCHAR(36) NULL;

ALTER TABLE food_orders ADD CONSTRAINT fk_food_orders_address FOREIGN KEY(address_id) REFERENCES addresses (id) ON DELETE SET NULL;

ALTER TABLE food_orders ADD COLUMN checkout_key VARCHAR(36);

ALTER TABLE food_orders ADD COLUMN checkout_fingerprint VARCHAR(64);

ALTER TABLE food_orders ADD COLUMN currency VARCHAR(3) NOT NULL DEFAULT 'EGP';

ALTER TABLE food_orders ADD CONSTRAINT uq_order_user_checkout_key UNIQUE (user_id, checkout_key);

CREATE INDEX ix_food_orders_restaurant_created ON food_orders (restaurant_id, created_at);

ALTER TABLE food_orders MODIFY subtotal NUMERIC(12, 2) NOT NULL;

ALTER TABLE food_orders MODIFY delivery_fee NUMERIC(12, 2) NOT NULL;

ALTER TABLE food_orders MODIFY total NUMERIC(12, 2) NOT NULL;

ALTER TABLE food_orders ADD CONSTRAINT ck_order_amounts CHECK (subtotal >= 0 AND delivery_fee >= 0);

ALTER TABLE food_orders ADD CONSTRAINT ck_order_total CHECK (total = subtotal + delivery_fee);

ALTER TABLE food_orders DROP COLUMN payment_status;

ALTER TABLE payments MODIFY amount NUMERIC(12, 2) NOT NULL;

ALTER TABLE payments ADD CONSTRAINT ck_payment_amount CHECK (amount >= 0);

UPDATE payments SET provider = 'simulation', status = 'simulated' WHERE provider = 'sandbox';

UPDATE alembic_version SET version_num='20261030_0003' WHERE alembic_version.version_num = '20261030_0002';

-- Running upgrade 20261030_0003 -> 20261031_0004

ALTER TABLE menu_items ADD COLUMN artwork VARCHAR(30) NOT NULL DEFAULT 'burger';

ALTER TABLE restaurants ADD COLUMN kind VARCHAR(20) NOT NULL DEFAULT 'restaurant';

CREATE INDEX ix_restaurants_kind ON restaurants (kind);

ALTER TABLE restaurants ADD COLUMN slug VARCHAR(80);

ALTER TABLE restaurants ADD COLUMN logo VARCHAR(500);

ALTER TABLE restaurants ADD CONSTRAINT uq_restaurant_slug UNIQUE (slug);

ALTER TABLE restaurants ADD COLUMN artwork VARCHAR(30) NOT NULL DEFAULT 'burger';

CREATE TABLE browse_categories (
    code VARCHAR(40) NOT NULL,
    name VARCHAR(80) NOT NULL,
    artwork VARCHAR(30) NOT NULL,
    PRIMARY KEY (code)
);

CREATE TABLE restaurant_categories (
    restaurant_id VARCHAR(36) NOT NULL,
    category_code VARCHAR(40) NOT NULL,
    PRIMARY KEY (restaurant_id, category_code),
    FOREIGN KEY(restaurant_id) REFERENCES restaurants (id) ON DELETE CASCADE,
    FOREIGN KEY(category_code) REFERENCES browse_categories (code) ON DELETE CASCADE
);

CREATE TABLE favorite_restaurants (
    user_id VARCHAR(36) NOT NULL,
    restaurant_id VARCHAR(36) NOT NULL,
    PRIMARY KEY (user_id, restaurant_id),
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY(restaurant_id) REFERENCES restaurants (id) ON DELETE CASCADE
);

ALTER TABLE carts ADD CONSTRAINT uq_cart_user_restaurant UNIQUE (user_id, restaurant_id);

DROP INDEX ix_carts_user_id ON carts;

CREATE INDEX ix_carts_user_id ON carts (user_id);

ALTER TABLE carts ADD COLUMN revision INTEGER NOT NULL DEFAULT '0';

ALTER TABLE food_orders ADD COLUMN cart_id VARCHAR(36);

ALTER TABLE food_orders ADD CONSTRAINT fk_order_cart FOREIGN KEY(cart_id) REFERENCES carts (id) ON DELETE SET NULL;

ALTER TABLE food_orders ADD COLUMN cart_revision INTEGER;

ALTER TABLE payments ADD COLUMN provider_order_id VARCHAR(80);

ALTER TABLE payments ADD COLUMN intention_id VARCHAR(100);

ALTER TABLE payments ADD COLUMN checkout_token TEXT;

ALTER TABLE payments ADD COLUMN expires_at DATETIME;

ALTER TABLE payments ADD COLUMN transaction_id VARCHAR(80);

ALTER TABLE payments ADD COLUMN claimed_reference VARCHAR(100);

ALTER TABLE payments ADD COLUMN verified_reference VARCHAR(100);

ALTER TABLE payments ADD CONSTRAINT uq_payment_provider_order_id UNIQUE (provider_order_id);

ALTER TABLE payments ADD CONSTRAINT uq_payment_intention_id UNIQUE (intention_id);

ALTER TABLE payments ADD CONSTRAINT uq_payment_transaction_id UNIQUE (transaction_id);

ALTER TABLE payments ADD CONSTRAINT uq_payment_verified_reference UNIQUE (verified_reference);

ALTER TABLE payments ADD COLUMN test_mode BOOL NOT NULL DEFAULT '0';

ALTER TABLE payments ADD COLUMN transfer_recipient VARCHAR(120);

ALTER TABLE payments ADD COLUMN transfer_recipient_name VARCHAR(160);

CREATE TABLE order_events (
    id VARCHAR(36) NOT NULL,
    order_id VARCHAR(36) NOT NULL,
    status VARCHAR(30) NOT NULL,
    actor_id VARCHAR(36),
    note VARCHAR(300),
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(order_id) REFERENCES food_orders (id) ON DELETE CASCADE,
    FOREIGN KEY(actor_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_order_events_order_id ON order_events (order_id);

INSERT INTO order_events (id, order_id, status, created_at) SELECT UUID(), id, status, created_at FROM food_orders;

CREATE TABLE payment_events (
    id VARCHAR(64) NOT NULL,
    payment_id VARCHAR(36) NOT NULL,
    transaction_id VARCHAR(80) NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(payment_id) REFERENCES payments (id) ON DELETE CASCADE
);

CREATE INDEX ix_payment_events_payment_id ON payment_events (payment_id);

UPDATE alembic_version SET version_num='20261031_0004' WHERE alembic_version.version_num = '20261030_0003';

-- Running upgrade 20261031_0004 -> 20261031_0005

ALTER TABLE restaurants MODIFY artwork VARCHAR(2048) NOT NULL DEFAULT 'burger';

ALTER TABLE menu_items MODIFY artwork VARCHAR(2048) NOT NULL DEFAULT 'burger';

UPDATE alembic_version SET version_num='20261031_0005' WHERE alembic_version.version_num = '20261031_0004';

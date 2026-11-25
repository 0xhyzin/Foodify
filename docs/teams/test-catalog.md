# فهرس حالات الاختبار الفعلية

الفهرس ده مولّد من تقارير JUnit الناتجة عن تشغيل الاختبارات، وليس من عدد دوال المصدر. الحالات Parameterized تُعد منفصلة لأن كل قيمة تتحقق من سلوك مختلف.

شرح الهدف من المجموعات وطريقة عزلها في [Unit وIntegration Tests](testing.md). أسماء الحالات الإنجليزية هي أسماء السيناريوهات الفعلية داخل ملفات الاختبار.

| المجموعة | الحالات | ناجح | فاشل | متجاهل |
|---|---:|---:|---:|---:|
| Backend — Unit | 55 | 55 | 0 | 0 |
| Backend — Integration | 152 | 152 | 0 | 0 |
| Frontend — Unit | 49 | 49 | 0 | 0 |
| Frontend — Integration | 10 | 10 | 0 | 0 |
| Vercel proxy — isolated handler | 12 | 12 | 0 | 0 |
| Postman — contracts | 7 | 7 | 0 | 0 |

## Backend — Unit

| السيناريو | النتيجة |
|---|---|
| `test_money_rounds_at_the_currency_boundary[12.345-12.35]` | ناجح |
| `test_money_rounds_at_the_currency_boundary[12.344-12.34]` | ناجح |
| `test_money_rounds_at_the_currency_boundary[0.005-0.01]` | ناجح |
| `test_money_rounds_at_the_currency_boundary[0-0.00]` | ناجح |
| `test_empty_cart_does_not_charge_delivery` | ناجح |
| `test_cart_mapping_uses_decimal_quantities_and_restaurant_availability[True-True]` | ناجح |
| `test_cart_mapping_uses_decimal_quantities_and_restaurant_availability[False-False]` | ناجح |
| `test_confirmation_transaction_commits_only_with_issued_session[None]` | ناجح |
| `test_confirmation_transaction_commits_only_with_issued_session[issuer]` | ناجح |
| `test_confirmation_transaction_commits_only_with_issued_session[commit]` | ناجح |
| `test_render_action_email_builds_safe_html_and_plain_text` | ناجح |
| `test_smtp_sender_attaches_rfc_headers_html_part_and_normalizes_gmail_app_password` | ناجح |
| `test_smtp_sender_raises_unavailable_when_recipient_is_refused` | ناجح |
| `test_brevo_sender_includes_html_and_rejects_non_201_202` | ناجح |
| `test_resend_adapter_dispatches_and_handles_errors` | ناجح |
| `test_free_webmail_via_third_party_relay_logs_dmarc_warning` | ناجح |
| `test_unsigned_or_invalid_hmac_cannot_settle_payment[]` | ناجح |
| `test_unsigned_or_invalid_hmac_cannot_settle_payment[00]` | ناجح |
| `test_unsigned_or_invalid_hmac_cannot_settle_payment[signature2]` | ناجح |
| `test_unsigned_or_invalid_hmac_cannot_settle_payment[signature3]` | ناجح |
| `test_missing_signed_field_is_invalid_callback` | ناجح |
| `test_signed_provider_error_cannot_mark_payment_paid` | ناجح |
| `test_capture_is_settlement_and_authorization_alone_is_not` | ناجح |
| `test_malformed_success_response_is_uncertain_and_must_not_be_retried[changes0]` | ناجح |
| `test_malformed_success_response_is_uncertain_and_must_not_be_retried[changes1]` | ناجح |
| `test_malformed_success_response_is_uncertain_and_must_not_be_retried[changes2]` | ناجح |
| `test_malformed_success_response_is_uncertain_and_must_not_be_retried[changes3]` | ناجح |
| `test_malformed_success_response_is_uncertain_and_must_not_be_retried[changes4]` | ناجح |
| `test_provider_timeout_has_unknown_outcome` | ناجح |
| `test_inconsistent_order_total_is_rejected_before_contacting_provider` | ناجح |
| `test_signed_callback_status_rules[changes0-paid]` | ناجح |
| `test_signed_callback_status_rules[changes1-pending]` | ناجح |
| `test_signed_callback_status_rules[changes2-failed]` | ناجح |
| `test_signed_callback_status_rules[changes3-failed]` | ناجح |
| `test_signed_callback_status_rules[changes4-refunded]` | ناجح |
| `test_signed_callback_status_rules[changes5-refunded]` | ناجح |
| `test_tampering_with_signed_amount_is_rejected` | ناجح |
| `test_signed_but_malformed_callback_types_rejected[changes0]` | ناجح |
| `test_signed_but_malformed_callback_types_rejected[changes1]` | ناجح |
| `test_signed_but_malformed_callback_types_rejected[changes2]` | ناجح |
| `test_simulation_is_disabled_in_production` | ناجح |
| `test_redis_limiter_hashes_identifiers_and_sets_retry_after` | ناجح |
| `test_redis_failure_fails_closed` | ناجح |
| `test_notification_templates_cover_all_sprint3_events[order_accepted]` | ناجح |
| `test_notification_templates_cover_all_sprint3_events[order_rejected]` | ناجح |
| `test_notification_templates_cover_all_sprint3_events[order_preparing]` | ناجح |
| `test_notification_templates_cover_all_sprint3_events[order_ready_for_pickup]` | ناجح |
| `test_notification_templates_cover_all_sprint3_events[delivery_assigned]` | ناجح |
| `test_notification_templates_cover_all_sprint3_events[delivery_reassigned]` | ناجح |
| `test_notification_templates_cover_all_sprint3_events[order_picked_up]` | ناجح |
| `test_notification_templates_cover_all_sprint3_events[order_delivered]` | ناجح |
| `test_notification_templates_cover_all_sprint3_events[payment_failed]` | ناجح |
| `test_notification_templates_cover_all_sprint3_events[order_cancelled]` | ناجح |
| `test_notification_templates_cover_all_sprint3_events[order_assigned_to_preparer]` | ناجح |
| `test_notification_templates_cover_all_sprint3_events[order_ready_for_courier_pickup]` | ناجح |

## Backend — Integration

| السيناريو | النتيجة |
|---|---|
| `test_registration_is_generic_and_does_not_issue_session` | ناجح |
| `test_duplicate_registration_is_indistinguishable_and_creates_no_duplicate` | ناجح |
| `test_email_normalization_and_customer_role` | ناجح |
| `test_invalid_registration_is_rejected[payload0]` | ناجح |
| `test_invalid_registration_is_rejected[payload1]` | ناجح |
| `test_invalid_registration_is_rejected[payload2]` | ناجح |
| `test_invalid_registration_is_rejected[payload3]` | ناجح |
| `test_invalid_registration_is_rejected[payload4]` | ناجح |
| `test_invalid_registration_is_rejected[payload5]` | ناجح |
| `test_malformed_json_is_rejected_without_input_echo` | ناجح |
| `test_unverified_customer_cannot_password_login` | ناجح |
| `test_browser_confirmation_issues_session_and_does_not_expose_refresh_token` | ناجح |
| `test_browser_confirmation_requires_origin_and_client_header[headers0]` | ناجح |
| `test_browser_confirmation_requires_origin_and_client_header[headers1]` | ناجح |
| `test_browser_confirmation_requires_origin_and_client_header[headers2]` | ناجح |
| `test_expired_or_used_proof_cannot_create_session[-1-False]` | ناجح |
| `test_expired_or_used_proof_cannot_create_session[10-True]` | ناجح |
| `test_legacy_confirmation_confirms_without_creating_session` | ناجح |
| `test_confirmation_rolls_back_when_session_issuance_fails` | ناجح |
| `test_valid_login_issues_bound_jwt_without_password` | ناجح |
| `test_wrong_credentials_share_generic_error` | ناجح |
| `test_logout_revokes_current_access` | ناجح |
| `test_browser_refresh_rotates_cookie_and_revokes_reuse` | ناجح |
| `test_reusing_rotated_refresh_token_revokes_the_whole_session` | ناجح |
| `test_forgot_password_is_generic` | ناجح |
| `test_reset_password_revokes_existing_session` | ناجح |
| `test_google_new_customer_receives_session_with_incomplete_profile` | ناجح |
| `test_google_email_match_does_not_silently_link_existing_password_account` | ناجح |
| `test_wrong_browser_binding_cannot_exchange_google_ticket` | ناجح |
| `test_unverified_provider_email_requires_email_proof` | ناجح |
| `test_replayed_oauth_state_is_rejected` | ناجح |
| `test_unconfigured_provider_has_no_authorization_url` | ناجح |
| `test_cart_quantities_totals_and_independent_restaurants` | ناجح |
| `test_repeated_add_coalesces_one_line` | ناجح |
| `test_cart_quantity_bounds_and_strict_type[0]` | ناجح |
| `test_cart_quantity_bounds_and_strict_type[-1]` | ناجح |
| `test_cart_quantity_bounds_and_strict_type[100]` | ناجح |
| `test_cart_quantity_bounds_and_strict_type[True]` | ناجح |
| `test_cart_quantity_bounds_and_strict_type[1.5]` | ناجح |
| `test_cart_quantity_bounds_and_strict_type[2]` | ناجح |
| `test_cart_cannot_exceed_quantity_limit_by_repeated_add` | ناجح |
| `test_item_from_another_restaurant_cannot_enter_cart` | ناجح |
| `test_other_account_cannot_mutate_or_observe_customer_cart` | ناجح |
| `test_remove_item_preserves_other_lines` | ناجح |
| `test_cash_checkout_snapshots_data_and_clears_only_its_cart` | ناجح |
| `test_checkout_replay_returns_one_order_even_after_cart_cleared` | ناجح |
| `test_idempotency_key_reuse_for_changed_payload_rejected` | ناجح |
| `test_checkout_stale_cart_revision_rejected` | ناجح |
| `test_checkout_cannot_trust_client_total` | ناجح |
| `test_checkout_rejects_price_change_after_review` | ناجح |
| `test_checkout_rejects_unavailable_item` | ناجح |
| `test_checkout_rejects_other_customers_address` | ناجح |
| `test_online_checkout_preserves_cart_until_verified_payment` | ناجح |
| `test_orders_history_and_details_are_owned` | ناجح |
| `test_operations_enforces_sequential_tracking_and_records_cash_settlement` | ناجح |
| `test_unpaid_online_order_cannot_start_fulfillment` | ناجح |
| `test_duplicate_callback_settles_once_and_clears_unchanged_cart` | ناجح |
| `test_settlement_preserves_cart_changed_during_payment` | ناجح |
| `test_signed_callback_must_match_recorded_order[changes0]` | ناجح |
| `test_signed_callback_must_match_recorded_order[changes1]` | ناجح |
| `test_signed_callback_must_match_recorded_order[changes2]` | ناجح |
| `test_late_failure_cannot_revert_paid_order` | ناجح |
| `test_second_settled_transaction_requires_reconciliation` | ناجح |
| `test_browser_return_query_cannot_mark_order_paid` | ناجح |
| `test_paymob_item_quantities_produce_exact_total_and_encrypted_checkout` | ناجح |
| `test_provider_rejection_and_uncertain_outcomes_differ[400-payment_setup_rejected]` | ناجح |
| `test_provider_rejection_and_uncertain_outcomes_differ[401-payment_setup_rejected]` | ناجح |
| `test_provider_rejection_and_uncertain_outcomes_differ[406-payment_setup_rejected]` | ناجح |
| `test_provider_rejection_and_uncertain_outcomes_differ[500-payment_initialization_unknown]` | ناجح |
| `test_payment_service_does_not_retry_uncertain_intentions[payment_setup_rejected-pending]` | ناجح |
| `test_payment_service_does_not_retry_uncertain_intentions[payment_initialization_unknown-initialization_unknown]` | ناجح |
| `test_existing_checkout_is_reopened_without_new_intention` | ناجح |
| `test_customer_claim_is_not_payment_confirmation` | ناجح |
| `test_unknown_provider_order_requests_callback_retry_without_writing_event` | ناجح |
| `test_refund_must_match_settled_transaction_and_does_not_corrupt_payment` | ناجح |
| `test_refund_callback_is_idempotent_and_cannot_be_undone_by_paid_callback` | ناجح |
| `test_another_customer_cannot_start_or_claim_payment_for_owned_order` | ناجح |
| `test_bank_transaction_reference_cannot_settle_two_orders` | ناجح |
| `test_provider_transaction_identifier_cannot_settle_two_orders` | ناجح |
| `test_get_current_profile` | ناجح |
| `test_update_profile_name_and_phone` | ناجح |
| `test_profile_rejects_invalid_or_privileged_fields[payload0]` | ناجح |
| `test_profile_rejects_invalid_or_privileged_fields[payload1]` | ناجح |
| `test_profile_rejects_invalid_or_privileged_fields[payload2]` | ناجح |
| `test_profile_rejects_invalid_or_privileged_fields[payload3]` | ناجح |
| `test_profile_rejects_invalid_or_privileged_fields[payload4]` | ناجح |
| `test_profile_rejects_invalid_or_privileged_fields[payload5]` | ناجح |
| `test_first_address_becomes_default_and_completes_profile` | ناجح |
| `test_address_ownership_cannot_be_changed_or_read_by_other_customer` | ناجح |
| `test_update_and_delete_owned_address` | ناجح |
| `test_invalid_coordinates_rejected[change0]` | ناجح |
| `test_invalid_coordinates_rejected[change1]` | ناجح |
| `test_invalid_coordinates_rejected[change2]` | ناجح |
| `test_customer_cannot_read_operational_restaurant_orders` | ناجح |
| `test_customer_cannot_update_operational_order_status` | ناجح |
| `test_operator_can_read_restaurant_order_list` | ناجح |
| `test_list_returns_database_catalog` | ناجح |
| `test_catalog_filters[category=burgers-expected0]` | ناجح |
| `test_catalog_filters[search=BURGER-expected1]` | ناجح |
| `test_catalog_filters[search=milk-expected2]` | ناجح |
| `test_catalog_filters[kind=grocery-expected3]` | ناجح |
| `test_catalog_filters[free_delivery=true-expected4]` | ناجح |
| `test_catalog_filters[max_delivery_minutes=25-expected5]` | ناجح |
| `test_catalog_filters[category=unknown-expected6]` | ناجح |
| `test_catalog_filters[search=unmatched-expected7]` | ناجح |
| `test_catalog_filters[category=burgers&search=milk-expected8]` | ناجح |
| `test_sort_and_pagination` | ناجح |
| `test_unbounded_or_unknown_query_rejected[limit=0]` | ناجح |
| `test_unbounded_or_unknown_query_rejected[limit=101]` | ناجح |
| `test_unbounded_or_unknown_query_rejected[offset=-1]` | ناجح |
| `test_unbounded_or_unknown_query_rejected[sort=arbitrary]` | ناجح |
| `test_unbounded_or_unknown_query_rejected[kind=invalid]` | ناجح |
| `test_details_and_menu_categories` | ناجح |
| `test_unknown_restaurant_returns_404[]` | ناجح |
| `test_unknown_restaurant_returns_404[/menu]` | ناجح |
| `test_unknown_restaurant_returns_404[/categories]` | ناجح |
| `test_menu_fields_and_category_filter` | ناجح |
| `test_inactive_restaurant_hidden` | ناجح |
| `test_favorite_is_idempotent_and_user_owned` | ناجح |
| `test_password_uses_argon2id` | ناجح |
| `test_profile_rejects_missing_or_invalid_bearer[headers0]` | ناجح |
| `test_profile_rejects_missing_or_invalid_bearer[headers1]` | ناجح |
| `test_profile_rejects_missing_or_invalid_bearer[headers2]` | ناجح |
| `test_tampered_token_rejected` | ناجح |
| `test_token_signed_with_wrong_secret_rejected` | ناجح |
| `test_expired_token_rejected` | ناجح |
| `test_wrong_token_context_rejected[aud-another-client]` | ناجح |
| `test_wrong_token_context_rejected[iss-another-issuer]` | ناجح |
| `test_wrong_token_context_rejected[type-refresh]` | ناجح |
| `test_deactivated_account_cannot_use_existing_token` | ناجح |
| `test_unknown_route_is_structured` | ناجح |
| `test_untrusted_host_rejected` | ناجح |
| `test_security_headers_are_present` | ناجح |
| `test_disallowed_cors_origin_not_reflected` | ناجح |
| `test_allowed_cors_supports_cookie_transport` | ناجح |
| `test_admin_creates_staff_and_they_can_login_immediately` | ناجح |
| `test_admin_user_directory_permissions_and_filters` | ناجح |
| `test_admin_updates_roles_deactivates_sessions_and_blocks_self_demotion` | ناجح |
| `test_alembic_head_and_reference_seed_idempotency` | ناجح |
| `test_managed_restaurants_and_cross_restaurant_scoping` | ناجح |
| `test_manager_rejection_is_terminal_and_blocks_further_transitions` | ناجح |
| `test_delivery_assignment_validation_and_duplicate_guards` | ناجح |
| `test_reassignment_my_orders_isolation_and_post_pickup_lock` | ناجح |
| `test_courier_cannot_pickup_before_ready_or_bypass_transitions` | ناجح |
| `test_order_cancellation_rules_before_and_after_acceptance` | ناجح |
| `test_manager_can_create_and_update_restaurants_menu_items_and_staff` | ناجح |
| `test_preparer_assignment_kitchen_flow_and_courier_structured_address` | ناجح |
| `test_all_fulfillment_and_delivery_notifications_and_isolation` | ناجح |
| `test_rejection_and_cancellation_emit_expected_notifications` | ناجح |
| `test_notification_dispatch_failure_does_not_corrupt_order_transition` | ناجح |
| `test_payment_failure_notifies_customer_blocks_fulfillment_and_allows_retry` | ناجح |
| `test_rejected_instapay_transfer_emits_payment_failed_notification` | ناجح |

## Frontend — Unit

| السيناريو | النتيجة |
|---|---|
| `payment accepts an approved HTTPS Paymob checkout: eg.checkout.paymob.com` | ناجح |
| `payment accepts an approved HTTPS Paymob checkout: accept.paymob.com` | ناجح |
| `payment rejects HTTP` | ناجح |
| `payment rejects lookalike host` | ناجح |
| `payment rejects unexpected port` | ناجح |
| `payment rejects wrong checkout path` | ناجح |
| `payment rejects credentials` | ناجح |
| `payment rejects fragment` | ناجح |
| `payment rejects missing public key` | ناجح |
| `payment rejects missing client secret` | ناجح |
| `payment rejects duplicate public key` | ناجح |
| `payment rejects duplicate client secret` | ناجح |
| `payment rejects blank public key` | ناجح |
| `payment rejects blank client secret` | ناجح |
| `payment rejects invalid URL` | ناجح |
| `payment rejects expired link` | ناجح |
| `payment rejects invalid expiry` | ناجح |
| `payment preserves an uncertain gateway failure instead of making another attempt` | ناجح |
| `local canonical origin preserves the OAuth/action path, query, and fragment` | ناجح |
| `origin redirect leaves unrelated origin untouched: http://127.0.0.1:5173` | ناجح |
| `origin redirect leaves unrelated origin untouched: https://foodify.example` | ناجح |
| `origin redirect leaves unrelated origin untouched: http://localhost:4173` | ناجح |
| `external /verify-email action reaches its HashRouter page` | ناجح |
| `external /reset-password action reaches its HashRouter page` | ناجح |
| `external /oauth/callback action reaches its HashRouter page` | ناجح |
| `external /oauth/callback action reaches its HashRouter page` | ناجح |
| `normalization does not turn an unrelated page into an auth action` | ناجح |
| `parallel session restores share one cookie rotation` | ناجح |
| `a late refresh 401 cannot erase a newly confirmed or OAuth session` | ناجح |
| `a late refresh success cannot restore a cleared session` | ناجح |
| `logout waits for an in-flight cookie rotation before clearing the server cookie` | ناجح |
| `malformed browser session is rejected before accepting access credentials` | ناجح |
| `a rejected request from customer A is never retried as customer B` | ناجح |
| `an expired request reuses a token already refreshed for the same customer` | ناجح |
| `email confirmation uses browser-session endpoint and continues to profile onboarding` | ناجح |
| `OAuth exchange requires the verifier retained by the originating browser tab` | ناجح |
| `Google OAuth exchange accepts the browser session and removes its one-use verifier` | ناجح |
| `OAuth start rejects an unapproved google authorization destination: https://accounts.google.com.attacker.invalid/o/oauth2/v2/auth` | ناجح |
| `OAuth start rejects an unapproved google authorization destination: http://accounts.google.com/o/oauth2/v2/auth` | ناجح |
| `OAuth start rejects an unapproved google authorization destination: https://user:password@accounts.google.com/o/oauth2/v2/auth` | ناجح |
| `OAuth start rejects an unapproved facebook authorization destination: https://www.facebook.com/unexpected` | ناجح |
| `cart rejects invalid quantity 0 before HTTP` | ناجح |
| `cart rejects invalid quantity -1 before HTTP` | ناجح |
| `cart rejects invalid quantity 1.5 before HTTP` | ناجح |
| `cart rejects invalid quantity 100 before HTTP` | ناجح |
| `cart rejects invalid quantity NaN before HTTP` | ناجح |
| `cart update preserves merchant scope and checkout passes server revision and idempotency key` | ناجح |
| `operations only advances active fulfillment stages and never reopens cancelled or unpaid orders` | ناجح |
| `role stage helpers separate manager, kitchen, and courier transitions strictly` | ناجح |

## Frontend — Integration

| السيناريو | النتيجة |
|---|---|
| `confirmation composes HTTP, DTO mapping, session acceptance and onboarding routing` | ناجح |
| `protected API rejection rotates the real session manager and retries once with its new token` | ناجح |
| `cart HTTP repositories preserve merchant identifiers and exact money strings through mapping` | ناجح |
| `checkout use case composes its HTTP DTO, idempotency header and mapped order response` | ناجح |
| `payment HTTP response passes through the real Paymob destination and expiry validator` | ناجح |
| `checkout conflicts retain server error codes and request IDs through the HTTP boundary` | ناجح |
| `order cancel and Sprint 3 structured address, transaction IDs, preparer, and courier fields map cleanly` | ناجح |
| `delivery repository covers couriers, assign/reassign, my-orders, and courier PICKED_UP/DELIVERED status` | ناجح |
| `notification and operations repositories cover unread inbox, restaurant/menu creation, preparers, and kitchen flow` | ناجح |
| `operations repository covers admin listUsers, createStaff, and updateUserRoles contracts` | ناجح |

## Vercel proxy — isolated handler

| السيناريو | النتيجة |
|---|---|
| `forwards catalog filters to the fixed backend and removes rewrite parameters` | ناجح |
| `forwards authentication, cookies, browser marker and idempotency without arbitrary headers` | ناجح |
| `signs the platform client IP and never forwards a browser supplied signature` | ناجح |
| `does not sign an invalid client IP` | ناجح |
| `forwards multiple refresh cookies and safe upstream response headers` | ناجح |
| `rejects duplicate API paths and path traversal without contacting the backend` | ناجح |
| `rejects missing, HTTP, credentialed and path-bearing backend origins` | ناجح |
| `rejects unsupported HTTP methods before contacting the backend` | ناجح |
| `limits parsed and streamed request bodies to one MiB` | ناجح |
| `does not forward an unexpected backend redirect` | ناجح |
| `returns a safe retryable error when the backend connection fails` | ناجح |
| `preserves a successful empty response for logout` | ناجح |

## Postman — contracts

| السيناريو | النتيجة |
|---|---|
| `Foodify.postman_collection.json uses one /api/v1 prefix with the shared environment origin` | ناجح |
| `Foodify.Sprint2.postman_collection.json uses one /api/v1 prefix with the shared environment origin` | ناجح |
| `Foodify.Sprint3.postman_collection.json uses one /api/v1 prefix with the shared environment origin` | ناجح |
| `all Postman environments define a backend origin without a path prefix` | ناجح |
| `browser email confirmation reference uses the protected session transport` | ناجح |
| `browser login references the credential variables already supplied by each environment` | ناجح |
| `Sprint 3 Postman collection covers admin, kitchen, delivery, and notifications portals` | ناجح |

"""Owner account seeded on first start when the database has no users. Only the scrypt HASH is stored here.
Change the password after your first sign-in (Settings > Team & Access > My security), or replace this file / use MSANII_ADMIN_EMAIL + MSANII_ADMIN_PASSWORD."""
OWNER_EMAIL = "owner@msanii.local"
OWNER_HASH = "scrypt:32768:8:1$Uvkxvra4weOOYlwJ$17509f94cc3540ff7adee580f8edda939345db6736a52112b91c8c69e52afb69b88bcde7c8b3c76a9084b11519e0d4f9ca8a8535621c4d4f4b59401d662b97a7"

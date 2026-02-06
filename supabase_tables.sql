-- Crear todas las tablas de Django en Supabase con estructura compatible

-- django_content_type
CREATE TABLE IF NOT EXISTS public.django_content_type (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  app_label character varying NOT NULL,
  model character varying NOT NULL,
  CONSTRAINT django_content_type_pkey PRIMARY KEY (id),
  CONSTRAINT django_content_type_app_label_model_key UNIQUE (app_label, model)
);

-- auth_group
CREATE TABLE IF NOT EXISTS public.auth_group (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  name character varying NOT NULL UNIQUE,
  CONSTRAINT auth_group_pkey PRIMARY KEY (id)
);

-- auth_permission
CREATE TABLE IF NOT EXISTS public.auth_permission (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  content_type_id bigint NOT NULL,
  codename character varying NOT NULL,
  name character varying NOT NULL,
  CONSTRAINT auth_permission_pkey PRIMARY KEY (id),
  CONSTRAINT auth_permission_content_type_id_fkey FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id),
  CONSTRAINT auth_permission_content_type_id_codename_key UNIQUE (content_type_id, codename)
);

-- auth_user (para el admin de Django)
CREATE TABLE IF NOT EXISTS public.auth_user (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  password character varying NOT NULL,
  last_login timestamp without time zone,
  is_superuser boolean NOT NULL DEFAULT false,
  username character varying NOT NULL UNIQUE,
  first_name character varying NOT NULL DEFAULT '',
  last_name character varying NOT NULL DEFAULT '',
  email character varying NOT NULL DEFAULT '',
  is_staff boolean NOT NULL DEFAULT false,
  is_active boolean NOT NULL DEFAULT true,
  date_joined timestamp without time zone NOT NULL DEFAULT now(),
  CONSTRAINT auth_user_pkey PRIMARY KEY (id)
);

-- django_session
CREATE TABLE IF NOT EXISTS public.django_session (
  session_key character varying NOT NULL,
  session_data text NOT NULL,
  expire_date timestamp without time zone NOT NULL,
  CONSTRAINT django_session_pkey PRIMARY KEY (session_key)
);

-- django_admin_log
CREATE TABLE IF NOT EXISTS public.django_admin_log (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  object_id text,
  object_repr character varying NOT NULL,
  action_flag smallint NOT NULL,
  change_message text NOT NULL DEFAULT '',
  content_type_id bigint,
  user_id bigint NOT NULL,
  action_time timestamp without time zone NOT NULL DEFAULT now(),
  CONSTRAINT django_admin_log_pkey PRIMARY KEY (id),
  CONSTRAINT django_admin_log_content_type_id_fkey FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id),
  CONSTRAINT django_admin_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_user(id)
);

-- auth_group_permissions
CREATE TABLE IF NOT EXISTS public.auth_group_permissions (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  group_id bigint NOT NULL,
  permission_id bigint NOT NULL,
  CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id),
  CONSTRAINT auth_group_permissions_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.auth_group(id),
  CONSTRAINT auth_group_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id),
  CONSTRAINT auth_group_permissions_group_id_permission_id_key UNIQUE (group_id, permission_id)
);

-- auth_user_groups
CREATE TABLE IF NOT EXISTS public.auth_user_groups (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  user_id bigint NOT NULL,
  group_id bigint NOT NULL,
  CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id),
  CONSTRAINT auth_user_groups_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_user(id),
  CONSTRAINT auth_user_groups_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.auth_group(id),
  CONSTRAINT auth_user_groups_user_id_group_id_key UNIQUE (user_id, group_id)
);

-- auth_user_user_permissions
CREATE TABLE IF NOT EXISTS public.auth_user_user_permissions (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  user_id bigint NOT NULL,
  permission_id bigint NOT NULL,
  CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id),
  CONSTRAINT auth_user_user_permissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_user(id),
  CONSTRAINT auth_user_user_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id),
  CONSTRAINT auth_user_user_permissions_user_id_permission_id_key UNIQUE (user_id, permission_id)
);

-- django_migrations
CREATE TABLE IF NOT EXISTS public.django_migrations (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  app character varying NOT NULL,
  name character varying NOT NULL,
  applied timestamp without time zone NOT NULL DEFAULT now(),
  CONSTRAINT django_migrations_pkey PRIMARY KEY (id)
);

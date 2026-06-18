CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE app_user (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text UNIQUE NOT NULL,
  full_name text NOT NULL,
  role text NOT NULL DEFAULT 'analyst',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE company (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  domain text,
  headquarters text,
  investment_focus text,
  external_system_id text UNIQUE,
  confidence_score numeric DEFAULT 0.75,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE person (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid REFERENCES company(id),
  full_name text NOT NULL,
  title text,
  email text,
  linkedin_url text,
  confidence_score numeric DEFAULT 0.75,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE interaction (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid REFERENCES company(id),
  source_document_id uuid,
  interaction_type text NOT NULL DEFAULT 'meeting',
  interaction_date date,
  summary text NOT NULL,
  sentiment text,
  crm_record_ref text,
  contains_pii boolean NOT NULL DEFAULT false,
  metadata jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE document (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid REFERENCES company(id),
  interaction_id uuid REFERENCES interaction(id),
  file_name text NOT NULL,
  mime_type text NOT NULL,
  storage_uri text NOT NULL,
  source text NOT NULL DEFAULT 'upload',
  hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE chunk (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id uuid NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  chunk_index integer NOT NULL,
  content text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE vector_item (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  chunk_id uuid NOT NULL REFERENCES chunk(id) ON DELETE CASCADE,
  index_name text NOT NULL,
  vector_dim integer NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'
);

CREATE TABLE action_item (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  interaction_id uuid REFERENCES interaction(id),
  owner text,
  due_date date,
  description text NOT NULL,
  status text NOT NULL DEFAULT 'open'
);

CREATE TABLE relationship_edge (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL,
  source_type text NOT NULL,
  target_id uuid NOT NULL,
  target_type text NOT NULL,
  relationship_type text NOT NULL,
  strength numeric DEFAULT 0.5,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE prompt_template (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  module text NOT NULL,
  version text NOT NULL,
  system_prompt text NOT NULL,
  user_template text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(module, version)
);

CREATE TABLE prompt_run (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  prompt_template_id uuid REFERENCES prompt_template(id),
  provider text NOT NULL,
  model text NOT NULL,
  input_tokens integer NOT NULL,
  cached_input_tokens integer NOT NULL DEFAULT 0,
  output_tokens integer NOT NULL,
  estimated_cost_usd numeric NOT NULL,
  quality_score numeric,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE crm_sync_job (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  target_object text NOT NULL,
  mode text NOT NULL,
  status text NOT NULL,
  payload jsonb NOT NULL,
  response jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE crm_exports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  external_system_id text UNIQUE NOT NULL,
  target_object text NOT NULL DEFAULT 'Interaction',
  payload jsonb NOT NULL,
  source text NOT NULL DEFAULT 'irip',
  synced_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE interaction ENABLE ROW LEVEL SECURITY;
ALTER TABLE document ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunk ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_run ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_sync_job ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_exports ENABLE ROW LEVEL SECURITY;

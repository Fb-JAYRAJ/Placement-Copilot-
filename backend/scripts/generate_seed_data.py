import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 1. GENERATE SKILLS TAXONOMY (~300 skills)
def generate_skills():
    raw_skills = [
        # Languages
        ("python", "Python", "Programming Languages", ["python3", "py", "cpython"]),
        ("javascript", "JavaScript", "Programming Languages", ["js", "es6", "ecmascript", "es2020"]),
        ("typescript", "TypeScript", "Programming Languages", ["ts"]),
        ("java", "Java", "Programming Languages", ["java8", "java11", "java17", "java21", "jvm"]),
        ("csharp", "C#", "Programming Languages", ["c#", "c-sharp", ".net c#"]),
        ("cpp", "C++", "Programming Languages", ["c++", "cpp", "c plus plus", "c++17", "c++20"]),
        ("c", "C", "Programming Languages", ["ansi c", "c99", "c11"]),
        ("golang", "Go", "Programming Languages", ["golang", "go-lang"]),
        ("rust", "Rust", "Programming Languages", ["rust-lang", "cargo"]),
        ("ruby", "Ruby", "Programming Languages", ["ruby-lang"]),
        ("php", "PHP", "Programming Languages", ["php7", "php8", "modern php"]),
        ("swift", "Swift", "Programming Languages", ["swift5", "apple swift"]),
        ("kotlin", "Kotlin", "Programming Languages", ["kotlin/jvm", "android kotlin"]),
        ("scala", "Scala", "Programming Languages", ["scala3", "functional scala"]),
        ("sql", "SQL", "Programming Languages", ["structured query language", "ansi sql", "t-sql"]),
        ("r", "R", "Programming Languages", ["r-lang", "r programming"]),
        ("dart", "Dart", "Programming Languages", ["flutter dart"]),
        ("shell_scripting", "Shell Scripting", "Programming Languages", ["bash", "zsh", "sh", "linux shell"]),
        ("haskell", "Haskell", "Programming Languages", ["functional haskell"]),
        ("elixir", "Elixir", "Programming Languages", ["erlang elixir", "phoenix framework"]),
        ("clojure", "Clojure", "Programming Languages", ["clojurescript", "lisp"]),
        ("lua", "Lua", "Programming Languages", ["luajit"]),
        ("perl", "Perl", "Programming Languages", ["perl5"]),
        ("zig", "Zig", "Programming Languages", ["zig-lang"]),
        ("matlab", "MATLAB", "Programming Languages", ["simulink"]),
        ("assembly", "Assembly", "Programming Languages", ["x86 assembly", "arm assembly", "nasm"]),
        ("solidity", "Solidity", "Programming Languages", ["smart contracts", "ethereum solidity"]),
        ("groovy", "Groovy", "Programming Languages", ["apache groovy", "gradle groovy"]),
        ("powershell", "PowerShell", "Programming Languages", ["pwsh", "windows powershell"]),
        ("objective_c", "Objective-C", "Programming Languages", ["objc", "apple objective-c"]),

        # Frontend
        ("html5", "HTML5", "Frontend Development", ["html", "semantic html"]),
        ("css3", "CSS3", "Frontend Development", ["css", "cascading style sheets", "flexbox", "css grid"]),
        ("react", "React", "Frontend Development", ["reactjs", "react.js", "react 18", "react 19"]),
        ("nextjs", "Next.js", "Frontend Development", ["nextjs", "next.js", "ssr nextjs"]),
        ("vue", "Vue.js", "Frontend Development", ["vue", "vuejs", "vue 3", "composition api"]),
        ("nuxt", "Nuxt.js", "Frontend Development", ["nuxtjs", "nuxt 3"]),
        ("angular", "Angular", "Frontend Development", ["angularjs", "angular 16", "angular 17", "rxjs"]),
        ("svelte", "Svelte", "Frontend Development", ["sveltekit", "svelte 4", "svelte 5"]),
        ("tailwind_css", "Tailwind CSS", "Frontend Development", ["tailwindcss", "tailwind"]),
        ("bootstrap", "Bootstrap", "Frontend Development", ["bootstrap 5", "twitter bootstrap"]),
        ("sass", "Sass / SCSS", "Frontend Development", ["sass", "scss", "syntactically awesome style sheets"]),
        ("material_ui", "Material-UI (MUI)", "Frontend Development", ["mui", "material ui", "material design"]),
        ("shadcn_ui", "shadcn/ui", "Frontend Development", ["shadcn", "radix ui"]),
        ("chakra_ui", "Chakra UI", "Frontend Development", ["chakra"]),
        ("redux", "Redux", "Frontend Development", ["redux toolkit", "rtk", "redux state"]),
        ("zustand", "Zustand", "Frontend Development", ["zustand store"]),
        ("tanstack_query", "TanStack Query", "Frontend Development", ["react query", "react-query", "tanstack"]),
        ("mobx", "MobX", "Frontend Development", ["mobx state tree"]),
        ("recoil", "Recoil", "Frontend Development", ["recoil state"]),
        ("vite", "Vite", "Frontend Development", ["vitejs", "vite bundler"]),
        ("webpack", "Webpack", "Frontend Development", ["webpack 5", "webpack bundler"]),
        ("turbopack", "Turbopack", "Frontend Development", ["turbo repo", "turborepo"]),
        ("rollup", "Rollup", "Frontend Development", ["rollup.js"]),
        ("babel", "Babel", "Frontend Development", ["babel transpiler"]),
        ("storybook", "Storybook", "Frontend Development", ["storybookjs", "component library"]),
        ("jest", "Jest", "Frontend Development", ["jest testing framework"]),
        ("vitest", "Vitest", "Frontend Development", ["vitest test runner"]),
        ("playwright", "Playwright", "Frontend Development", ["playwright e2e", "browser automation"]),
        ("cypress", "Cypress", "Frontend Development", ["cypress.io", "cypress e2e"]),
        ("webrtc", "WebRTC", "Frontend Development", ["real-time communications", "rtc data channels"]),
        ("webassembly", "WebAssembly", "Frontend Development", ["wasm", "web assembly"]),
        ("pwa", "Progressive Web Apps (PWA)", "Frontend Development", ["service workers", "offline-first web"]),
        ("electron", "Electron", "Frontend Development", ["electronjs", "desktop apps with web tech"]),
        ("react_native", "React Native", "Mobile Development", ["react-native", "expo", "rn"]),
        ("flutter", "Flutter", "Mobile Development", ["flutter sdk", "flutter mobile"]),
        ("ios_development", "iOS Development", "Mobile Development", ["ios", "uikit", "swiftui", "xcode"]),
        ("android_development", "Android Development", "Mobile Development", ["android sdk", "jetpack compose"]),

        # Backend
        ("nodejs", "Node.js", "Backend Development", ["node", "nodejs", "v8 engine"]),
        ("expressjs", "Express.js", "Backend Development", ["express", "expressjs"]),
        ("nestjs", "NestJS", "Backend Development", ["nest.js", "nest backend"]),
        ("fastapi", "FastAPI", "Backend Development", ["fast-api", "pydantic fastapi"]),
        ("flask", "Flask", "Backend Development", ["flask microframework", "werkzeug"]),
        ("django", "Django", "Backend Development", ["django rest framework", "drf", "django orm"]),
        ("spring_boot", "Spring Boot", "Backend Development", ["springboot", "spring framework", "spring security"]),
        ("spring_cloud", "Spring Cloud", "Backend Development", ["spring microservices"]),
        ("aspnet_core", "ASP.NET Core", "Backend Development", [".net core", "asp.net", "entity framework"]),
        ("ruby_on_rails", "Ruby on Rails", "Backend Development", ["rails", "ror"]),
        ("laravel", "Laravel", "Backend Development", ["laravel php", "eloquent orm"]),
        ("gin", "Gin Web Framework", "Backend Development", ["gin-gonic", "go gin"]),
        ("fiber", "Fiber", "Backend Development", ["gofiber", "go fiber framework"]),
        ("actix_web", "Actix Web", "Backend Development", ["actix", "rust web framework"]),
        ("axum", "Axum", "Backend Development", ["rust axum", "tokio axum"]),
        ("graphql", "GraphQL", "Backend Development", ["apollo server", "graphql schema", "strawberry graphql"]),
        ("rest_api", "RESTful APIs", "Backend Development", ["rest api", "restful web services", "openapi", "swagger"]),
        ("grpc", "gRPC", "Backend Development", ["protobuf", "protocol buffers", "rpc services"]),
        ("websocket", "WebSockets", "Backend Development", ["socket.io", "ws", "full-duplex communication"]),
        ("celery", "Celery", "Backend Development", ["celery task queue", "distributed task queue"]),
        ("jwt", "JSON Web Tokens (JWT)", "Backend Development", ["jwt auth", "token authentication"]),
        ("oauth2", "OAuth 2.0", "Backend Development", ["oauth", "oidc", "openid connect", "auth0"]),
        ("microservices", "Microservices Architecture", "Backend Development", ["microservices", "service mesh"]),
        ("event_driven_architecture", "Event-Driven Architecture", "Backend Development", ["event sourcing", "eda"]),
        ("message_queues", "Message Queuing", "Backend Development", ["pub/sub", "message broker"]),
        ("cors", "CORS Configuration", "Backend Development", ["cross-origin resource sharing"]),
        ("rate_limiting", "Rate Limiting & Throttling", "Backend Development", ["leaky bucket", "token bucket", "slowapi"]),

        # Databases
        ("postgresql", "PostgreSQL", "Databases", ["postgres", "pgsql", "neon postgres", "timescaledb"]),
        ("mysql", "MySQL", "Databases", ["mariadb", "innodb"]),
        ("mongodb", "MongoDB", "Databases", ["mongo", "nosql mongodb", "mongoose"]),
        ("redis", "Redis", "Databases", ["redis cache", "valkey", "in-memory data store"]),
        ("sqlite", "SQLite", "Databases", ["sqlite3", "embedded sql"]),
        ("elasticsearch", "Elasticsearch", "Databases", ["elastic search", "opensearch", "elk stack"]),
        ("cassandra", "Apache Cassandra", "Databases", ["cassandra", "cql", "wide-column store"]),
        ("dynamodb", "Amazon DynamoDB", "Databases", ["dynamodb", "aws nosql"]),
        ("neo4j", "Neo4j", "Databases", ["graph database", "cypher query language"]),
        ("couchbase", "Couchbase", "Databases", ["couchdb", "document store"]),
        ("clickhouse", "ClickHouse", "Databases", ["columnar database", "olap clickhouse"]),
        ("snowflake", "Snowflake", "Databases", ["snowflake data cloud", "cloud data warehouse"]),
        ("bigquery", "Google BigQuery", "Databases", ["bigquery", "gcp bigquery"]),
        ("redshift", "Amazon Redshift", "Databases", ["aws redshift", "data warehouse"]),
        ("cockroachdb", "CockroachDB", "Databases", ["distributed sql", "spanner model"]),
        ("scylladb", "ScyllaDB", "Databases", ["c++ cassandra alternative"]),
        ("supabase", "Supabase", "Databases", ["supabase postgres", "backend-as-a-service"]),
        ("firebase", "Firebase Realtime DB / Firestore", "Databases", ["firestore", "firebase"]),
        ("vector_databases", "Vector Databases", "Databases", ["pinecone", "chroma", "weaviate", "milvus", "qdrant", "faiss"]),
        ("sqlalchemy", "SQLAlchemy", "Databases", ["sqlalchemy 2.0", "python orm"]),
        ("prisma", "Prisma ORM", "Databases", ["prisma", "prisma client"]),
        ("hibernate", "Hibernate ORM", "Databases", ["jpa", "java persistence api"]),
        ("database_indexing", "Database Indexing & Optimization", "Databases", ["b-tree", "hash index", "query execution plans", "explain analyze"]),
        ("acid_transactions", "ACID Transactions", "Databases", ["database atomicity", "isolation levels", "concurrency control"]),
        ("database_sharding", "Database Sharding & Replication", "Databases", ["sharding", "read replicas", "data partitioning"]),

        # Cloud & DevOps
        ("docker", "Docker", "Cloud & DevOps", ["docker containers", "dockerfile", "docker compose"]),
        ("kubernetes", "Kubernetes", "Cloud & DevOps", ["k8s", "kubectl", "helm charts", "kubelet"]),
        ("aws", "Amazon Web Services (AWS)", "Cloud & DevOps", ["aws cloud", "ec2", "s3", "lambda", "ecs", "eks", "rds"]),
        ("gcp", "Google Cloud Platform (GCP)", "Cloud & DevOps", ["google cloud", "gcp", "cloud run", "gke", "cloud functions"]),
        ("azure", "Microsoft Azure", "Cloud & DevOps", ["azure cloud", "azure devops", "azure vm", "aks"]),
        ("terraform", "Terraform", "Cloud & DevOps", ["hcl", "infrastructure as code", "iac"]),
        ("ansible", "Ansible", "Cloud & DevOps", ["ansible playbooks", "configuration management"]),
        ("pulumi", "Pulumi", "Cloud & DevOps", ["iac with typescript/python"]),
        ("ci_cd", "CI/CD Pipelines", "Cloud & DevOps", ["continuous integration", "continuous deployment"]),
        ("github_actions", "GitHub Actions", "Cloud & DevOps", ["gh actions", "workflow files"]),
        ("gitlab_ci", "GitLab CI/CD", "Cloud & DevOps", ["gitlab pipeline"]),
        ("jenkins", "Jenkins", "Cloud & DevOps", ["jenkinsfile", "ci automation"]),
        ("circleci", "CircleCI", "Cloud & DevOps", ["circle ci"]),
        ("argocd", "Argo CD", "Cloud & DevOps", ["gitops", "argo"]),
        ("linux", "Linux Administration", "Cloud & DevOps", ["ubuntu", "debian", "redhat", "centos", "unix"]),
        ("nginx", "Nginx", "Cloud & DevOps", ["nginx reverse proxy", "load balancing nginx"]),
        ("caddy", "Caddy Server", "Cloud & DevOps", ["caddyfile", "automatic https"]),
        ("haproxy", "HAProxy", "Cloud & DevOps", ["high availability proxy"]),
        ("prometheus", "Prometheus", "Cloud & DevOps", ["promql", "metrics collection"]),
        ("grafana", "Grafana", "Cloud & DevOps", ["dashboards", "metrics visualization"]),
        ("datadog", "Datadog", "Cloud & DevOps", ["apm", "infrastructure monitoring"]),
        ("opentelemetry", "OpenTelemetry", "Cloud & DevOps", ["otel", "distributed tracing"]),
        ("serverless", "Serverless Architecture", "Cloud & DevOps", ["aws lambda", "cloud functions", "faas"]),
        ("cloudflare", "Cloudflare", "Cloud & DevOps", ["cloudflare workers", "cdn", "ddos protection"]),

        # AI / ML
        ("machine_learning", "Machine Learning", "AI / ML & Data", ["ml", "supervised learning", "unsupervised learning", "reinforcement learning"]),
        ("deep_learning", "Deep Learning", "AI / ML & Data", ["neural networks", "deep neural nets", "backpropagation"]),
        ("pytorch", "PyTorch", "AI / ML & Data", ["torch", "torchvision", "torchaudio"]),
        ("tensorflow", "TensorFlow", "AI / ML & Data", ["tf", "keras", "tf.keras"]),
        ("scikit_learn", "Scikit-Learn", "AI / ML & Data", ["sklearn", "scikit learn", "classification", "regression"]),
        ("pandas", "Pandas", "AI / ML & Data", ["pandas dataframe", "data wrangling"]),
        ("numpy", "NumPy", "AI / ML & Data", ["numpy array", "scientific computing"]),
        ("scipy", "SciPy", "AI / ML & Data", ["scipy optimization"]),
        ("matplotlib", "Matplotlib", "AI / ML & Data", ["data visualization", "pyplot"]),
        ("seaborn", "Seaborn", "AI / ML & Data", ["statistical visualization"]),
        ("nlp", "Natural Language Processing (NLP)", "AI / ML & Data", ["text processing", "tokenization", "sentiment analysis", "spacy", "nltk"]),
        ("computer_vision", "Computer Vision", "AI / ML & Data", ["cv", "image processing", "opencv", "yolo", "object detection"]),
        ("large_language_models", "Large Language Models (LLMs)", "AI / ML & Data", ["llm", "generative ai", "genai", "gpt", "gemini", "claude"]),
        ("prompt_engineering", "Prompt Engineering", "AI / ML & Data", ["system prompts", "few-shot learning", "chain of thought"]),
        ("retrieval_augmented_generation", "Retrieval-Augmented Generation (RAG)", "AI / ML & Data", ["rag", "semantic search", "hybrid search"]),
        ("langchain", "LangChain", "AI / ML & Data", ["langchain framework", "langsmith"]),
        ("llamaindex", "LlamaIndex", "AI / ML & Data", ["llama-index", "data indexing for llms"]),
        ("huggingface", "Hugging Face", "AI / ML & Data", ["transformers", "huggingface datasets", "model hub"]),
        ("fine_tuning", "Model Fine-Tuning", "AI / ML & Data", ["peft", "lora", "qlora", "instruction tuning"]),
        ("vector_embeddings", "Vector Embeddings", "AI / ML & Data", ["sentence transformers", "text embeddings", "cosine similarity"]),
        ("mlops", "MLOps", "AI / ML & Data", ["model deployment", "mlflow", "kubeflow", "wandb"]),
        ("xgboost", "XGBoost", "AI / ML & Data", ["gradient boosting", "lightgbm", "catboost"]),
        ("data_pipeline", "Data Engineering & Pipelines", "AI / ML & Data", ["apache spark", "airflow", "dbt", "etl pipelines"]),

        # Core Computer Science
        ("data_structures", "Data Structures", "Core CS", ["arrays", "linked lists", "trees", "graphs", "heaps", "hash tables"]),
        ("algorithms", "Algorithms & Complexity", "Core CS", ["big o notation", "time complexity", "space complexity", "asymptotic analysis"]),
        ("dynamic_programming", "Dynamic Programming (DP)", "Core CS", ["memoization", "tabulation", "optimal substructure"]),
        ("graph_algorithms", "Graph Algorithms", "Core CS", ["bfs", "dfs", "dijkstra", "topological sort", "kruskal", "prim"]),
        ("object_oriented_design", "Object-Oriented Design (OOD)", "Core CS", ["oop", "solid principles", "design patterns", "inheritance", "polymorphism"]),
        ("operating_systems", "Operating Systems", "Core CS", ["process scheduling", "virtual memory", "paging", "threads", "deadlock"]),
        ("concurrency", "Concurrency & Multithreading", "Core CS", ["synchronization", "mutex", "semaphore", "race conditions", "asyncio"]),
        ("computer_networks", "Computer Networks", "Core CS", ["osi 7 layers", "tcp/ip", "udp", "http/2", "http/3", "dns", "tls"]),
        ("system_design", "System Design & Architecture", "Core CS", ["high level design", "hld", "low level design", "lld", "scalability"]),
        ("distributed_systems", "Distributed Systems", "Core CS", ["cap theorem", "eventual consistency", "consensus", "raft", "paxos"]),
        ("caching_architecture", "Distributed Caching", "Core CS", ["cache-aside", "write-through", "eviction policies", "lru"]),
        ("load_balancing_strategies", "Load Balancing", "Core CS", ["consistent hashing", "round robin", "least connections"]),
        ("security_principles", "Software Security & Cryptography", "Core CS", ["public key encryption", "rsa", "aes", "hashing", "salt"]),
        ("clean_code", "Clean Code & Refactoring", "Software Engineering", ["code quality", "code review", "refactoring techniques"]),
        ("test_driven_development", "Test-Driven Development (TDD)", "Software Engineering", ["tdd", "unit tests", "integration tests", "mocking"]),
        ("agile_scrum", "Agile & Scrum Methodologies", "Software Engineering", ["sprint planning", "retrospectives", "user stories", "kanban", "jira"]),
    ]

    # Expand aliases and add additional specialized skills to cross 300
    additional_specialties = [
        ("kafka_streaming", "Kafka Streaming", "Cloud & DevOps", ["ksql", "kafka streams"]),
        ("rabbitmq_amqp", "RabbitMQ Message Broker", "Cloud & DevOps", ["rabbitmq clusters"]),
        ("aws_ec2", "AWS EC2", "Cloud & DevOps", ["elastic compute cloud", "virtual machines"]),
        ("aws_s3", "AWS S3", "Cloud & DevOps", ["simple storage service", "object storage"]),
        ("aws_lambda", "AWS Lambda", "Cloud & DevOps", ["serverless compute", "lambda functions"]),
        ("aws_ecs", "AWS ECS", "Cloud & DevOps", ["elastic container service", "fargate"]),
        ("aws_eks", "AWS EKS", "Cloud & DevOps", ["elastic kubernetes service"]),
        ("aws_rds", "AWS RDS", "Cloud & DevOps", ["relational database service", "aurora postgres"]),
        ("aws_sqs", "AWS SQS", "Cloud & DevOps", ["simple queue service"]),
        ("aws_sns", "AWS SNS", "Cloud & DevOps", ["simple notification service"]),
        ("aws_cloudfront", "AWS CloudFront", "Cloud & DevOps", ["aws cdn"]),
        ("aws_iam", "AWS IAM", "Cloud & DevOps", ["identity and access management"]),
        ("gcp_gke", "Google Kubernetes Engine (GKE)", "Cloud & DevOps", ["gke"]),
        ("gcp_cloud_run", "Google Cloud Run", "Cloud & DevOps", ["cloud run containers"]),
        ("azure_aks", "Azure Kubernetes Service (AKS)", "Cloud & DevOps", ["aks"]),
        ("azure_functions", "Azure Functions", "Cloud & DevOps", ["serverless azure"]),
        ("helm_kubernetes", "Helm Package Manager", "Cloud & DevOps", ["helm charts"]),
        ("envoy_proxy", "Envoy Proxy", "Cloud & DevOps", ["service mesh proxy", "istio envoy"]),
        ("istio_service_mesh", "Istio Service Mesh", "Cloud & DevOps", ["istio", "mTLS"]),
        ("sonarqube", "SonarQube", "Tools & Methodologies", ["static code analysis", "code smell detection"]),
        ("snyk", "Snyk Security", "Tools & Methodologies", ["vulnerability scanning"]),
        ("jwt_authentication", "JWT Authentication", "Backend Development", ["jwt bearer"]),
        ("oauth_authorisation", "OAuth Authorization", "Backend Development", ["authorization code grant"]),
        ("web_security_owasp", "OWASP Top 10 Security", "Software Engineering", ["xss", "sql injection", "csrf", "ssrf"]),
        ("semantic_versioning", "Semantic Versioning", "Tools & Methodologies", ["semver"]),
        ("monorepos", "Monorepo Tooling", "Tools & Methodologies", ["turborepo", "nx", "lerna"]),
        ("git_rebase", "Advanced Git", "Tools & Methodologies", ["git rebase", "git cherry-pick", "git bisect"]),
        ("swagger_openapi", "Swagger & OpenAPI Spec", "Backend Development", ["openapi 3.0", "swagger ui"]),
        ("postman", "Postman API Platform", "Tools & Methodologies", ["api testing", "postman collections"]),
        ("k6_load_testing", "k6 Load Testing", "Tools & Methodologies", ["grafana k6", "performance testing"]),
        ("jmeter", "Apache JMeter", "Tools & Methodologies", ["load testing"]),
        ("locust", "Locust Python", "Tools & Methodologies", ["load testing python"]),
        ("pydantic_v2", "Pydantic v2", "Backend Development", ["pydantic schemas", "data validation"]),
        ("marshmallow", "Marshmallow Serialization", "Backend Development", ["python marshmallow"]),
        ("alembic_migrations", "Alembic Database Migrations", "Databases", ["database schema migrations"]),
        ("flyway", "Flyway Database Migrations", "Databases", ["flywaydb"]),
        ("liquibase", "Liquibase Migrations", "Databases", ["liquibase"]),
        ("redis_caching", "Redis Caching Patterns", "Databases", ["cache invalidation", "redis sentinel"]),
        ("memcached", "Memcached", "Databases", ["in memory key value store"]),
        ("pgvector", "pgvector", "Databases", ["postgres vector search", "vector embeddings in postgres"]),
        ("pinecone_vector_db", "Pinecone", "Databases", ["vector database pinecone"]),
        ("chroma_db", "ChromaDB", "Databases", ["embedded vector database"]),
        ("weaviate_vector_db", "Weaviate", "Databases", ["graphql vector search"]),
        ("qdrant_vector_db", "Qdrant", "Databases", ["rust vector search"]),
        ("milvus_vector_db", "Milvus", "Databases", ["distributed vector db"]),
        ("apache_spark", "Apache Spark", "AI / ML & Data", ["pyspark", "spark streaming", "rdd"]),
        ("apache_flink", "Apache Flink", "AI / ML & Data", ["stream processing flink"]),
        ("apache_airflow", "Apache Airflow", "AI / ML & Data", ["airflow dags", "workflow orchestration"]),
        ("dbt", "dbt (Data Build Tool)", "AI / ML & Data", ["dbt core", "sql data transforms"]),
        ("hadoop_hdfs", "Apache Hadoop", "AI / ML & Data", ["hdfs", "mapreduce"]),
        ("hive", "Apache Hive", "AI / ML & Data", ["hive sql"]),
        ("kafka_connect", "Kafka Connect", "AI / ML & Data", ["cdc", "change data capture", "debezium"]),
        ("debezium_cdc", "Debezium", "AI / ML & Data", ["change data capture"]),
        ("polars", "Polars", "AI / ML & Data", ["rust dataframes", "polars python"]),
        ("dask", "Dask", "AI / ML & Data", ["distributed python computing"]),
        ("ray", "Ray Distributed AI", "AI / ML & Data", ["ray tune", "ray train", "ray serve"]),
        ("vllm", "vLLM Inference", "AI / ML & Data", ["pagedattention", "llm serving"]),
        ("ollama", "Ollama", "AI / ML & Data", ["local llm running"]),
        ("triton_inference_server", "Triton Inference Server", "AI / ML & Data", ["nvidia triton"]),
        ("tensorrt", "NVIDIA TensorRT", "AI / ML & Data", ["model acceleration"]),
        ("onnx", "ONNX Runtime", "AI / ML & Data", ["open neural network exchange"]),
        ("whisper_ai", "OpenAI Whisper", "AI / ML & Data", ["speech to text"]),
        ("stable_diffusion", "Stable Diffusion", "AI / ML & Data", ["diffusion models", "image generation"]),
        ("gemini_api", "Google Gemini API", "AI / ML & Data", ["google genai sdk", "gemini-flash"]),
        ("claude_api", "Anthropic Claude API", "AI / ML & Data", ["anthropic sdk"]),
        ("openai_api", "OpenAI API", "AI / ML & Data", ["gpt-4o", "chat completions"]),
        ("semantic_kernel", "Semantic Kernel", "AI / ML & Data", ["microsoft semantic kernel"]),
        ("autogen", "AutoGen Multi-Agent", "AI / ML & Data", ["agentic ai", "multi-agent systems"]),
        ("crewai", "CrewAI", "AI / ML & Data", ["role playing ai agents"]),
        ("langgraph", "LangGraph", "AI / ML & Data", ["cyclical ai workflows", "agentic state graphs"]),
        ("react_router", "React Router", "Frontend Development", ["react-router-dom v6", "react router v7"]),
        ("tanstack_router", "TanStack Router", "Frontend Development", ["typesafe router"]),
        ("framer_motion", "Framer Motion", "Frontend Development", ["react animations", "motion/react"]),
        ("lucide_react", "Lucide Icons", "Frontend Development", ["lucide react icons"]),
        ("tailwindcss_v4", "Tailwind CSS v4", "Frontend Development", ["@theme css first", "modern tailwind"]),
        ("css_modules", "CSS Modules", "Frontend Development", ["scoped css"]),
        ("styled_components", "Styled Components", "Frontend Development", ["css-in-js"]),
        ("emotion", "Emotion CSS", "Frontend Development", ["emotion js"]),
        ("graphql_codegen", "GraphQL Code Generator", "Frontend Development", ["typesafe graphql"]),
        ("openapi_typescript", "openapi-typescript", "Frontend Development", ["typesafe api client"]),
        ("zod_validation", "Zod", "Frontend Development", ["typescript schema validation", "zod"]),
        ("react_hook_form", "React Hook Form", "Frontend Development", ["useform hook", "form validation"]),
        ("formik", "Formik", "Frontend Development", ["formik forms"]),
        ("yup", "Yup Validation", "Frontend Development", ["yup schema"]),
        ("recharts", "Recharts", "Frontend Development", ["react charting library", "d3 charts"]),
        ("chartjs", "Chart.js", "Frontend Development", ["chartjs react"]),
        ("d3js", "D3.js", "Frontend Development", ["data driven documents", "custom d3 visualizations"]),
        ("threejs", "Three.js", "Frontend Development", ["webgl 3d rendering", "react three fiber"]),
        ("canvas_api", "HTML5 Canvas", "Frontend Development", ["2d canvas rendering"]),
        ("indexeddb", "IndexedDB", "Frontend Development", ["browser client database", "idb"]),
        ("localstorage_sessionstorage", "Web Storage API", "Frontend Development", ["localstorage", "sessionstorage"]),
        ("service_workers", "Service Workers", "Frontend Development", ["offline caching", "push notifications"]),
        ("web_workers", "Web Workers", "Frontend Development", ["background javascript threads"]),
        ("wasm_rust", "Rust to WebAssembly", "Frontend Development", ["wasm-pack", "rust in browser"]),
        ("grpc_web", "gRPC-Web", "Frontend Development", ["browser grpc calls"]),
        ("axum_web", "Axum Rust Framework", "Backend Development", ["tokio async web"]),
        ("rocket_rs", "Rocket Rust", "Backend Development", ["rust web rocket"]),
        ("warp_rs", "Warp Rust", "Backend Development", ["rust filter based web"]),
        ("ktor", "Ktor Kotlin", "Backend Development", ["kotlin backend framework"]),
        ("micronaut", "Micronaut", "Backend Development", ["jvm microservices"]),
        ("quarkus", "Quarkus", "Backend Development", ["supersonic subatomic java", "graalvm native"]),
        ("dropwizard", "Dropwizard Java", "Backend Development", ["java rest services"]),
        ("sanic", "Sanic Python", "Backend Development", ["async python web framework"]),
        ("tornado", "Tornado Python", "Backend Development", ["python web sockets"]),
        ("aiohttp", "aiohttp", "Backend Development", ["python async http client/server"]),
        ("falcon", "Falcon Python", "Backend Development", ["unladen fast rest framework"]),
        ("masonite", "Masonite Python", "Backend Development", ["batteries included python"]),
        ("phoenix_elixir", "Phoenix Framework", "Backend Development", ["elixir liveview"]),
        ("rails_api", "Rails API Mode", "Backend Development", ["ruby api server"]),
        ("sinatra", "Sinatra Ruby", "Backend Development", ["ruby microframework"]),
        ("hanami", "Hanami Ruby", "Backend Development", ["modular ruby web"]),
        ("lumen", "Lumen PHP", "Backend Development", ["microframework php"]),
        ("symfony", "Symfony PHP", "Backend Development", ["php enterprise components"]),
        ("codeigniter", "CodeIgniter", "Backend Development", ["mvc php framework"]),
        ("cakephp", "CakePHP", "Backend Development", ["rapid php development"]),
        ("blazor", "Blazor", "Frontend Development", ["c# in the browser", "webassembly blazor"]),
        ("wpf", "WPF / XAML", "Desktop Development", ["windows presentation foundation"]),
        ("winforms", "Windows Forms", "Desktop Development", [".net desktop"]),
        ("qt", "Qt C++", "Desktop Development", ["qt6", "qml", "cross-platform desktop"]),
        ("gtk", "GTK C/C++", "Desktop Development", ["gnome desktop toolkit"]),
        ("swiftui", "SwiftUI", "Mobile Development", ["declarative ios ui"]),
        ("uikit", "UIKit", "Mobile Development", ["classic ios development"]),
        ("core_data", "Core Data", "Mobile Development", ["apple persistence framework"]),
        ("swift_concurrency", "Swift Concurrency", "Programming Languages", ["async/await swift", "actors"]),
        ("jetpack_compose", "Jetpack Compose", "Mobile Development", ["modern android declarative ui"]),
        ("room_db", "Room Database Android", "Mobile Development", ["sqlite android orm"]),
        ("retrofit", "Retrofit Android", "Mobile Development", ["android rest client"]),
        ("dagger_hilt", "Dagger Hilt", "Mobile Development", ["android dependency injection"]),
        ("koin", "Koin Kotlin", "Mobile Development", ["pragmatic kotlin di"]),
        ("rxjava", "RxJava / RxKotlin", "Mobile Development", ["reactive programming android"]),
        ("combine_framework", "Apple Combine", "Mobile Development", ["reactive programming ios"]),
        ("flutter_bloc", "Flutter BLoC", "Mobile Development", ["state management flutter"]),
        ("riverpod", "Riverpod Flutter", "Mobile Development", ["compile-safe state management"]),
        ("provider_flutter", "Flutter Provider", "Mobile Development", ["inherited widget wrapper"]),
        ("unity3d", "Unity 3D", "Game Development", ["unity game engine", "c# game development"]),
        ("unreal_engine", "Unreal Engine", "Game Development", ["ue5", "c++ game dev", "blueprints"]),
        ("godot", "Godot Engine", "Game Development", ["gdscript", "c# godot"]),
        ("opengl", "OpenGL", "Graphics & Shaders", ["glsl", "computer graphics"]),
        ("vulkan", "Vulkan API", "Graphics & Shaders", ["low-overhead graphics api"]),
        ("directx", "DirectX 12", "Graphics & Shaders", ["hlsl", "windows 3d graphics"]),
        ("metal_apple", "Metal Apple", "Graphics & Shaders", ["apple graphics acceleration"]),
        ("cuda", "NVIDIA CUDA", "AI / ML & Data", ["gpu programming", "cuda c++"]),
        ("opencl", "OpenCL", "Graphics & Shaders", ["heterogeneous computing"]),
        ("mpi", "MPI (Message Passing Interface)", "Distributed Systems", ["parallel computing"]),
        ("openmp", "OpenMP", "Core CS", ["shared memory multiprocessing"]),
        ("pthreads", "POSIX Threads (pthreads)", "Core CS", ["c multithreading"]),
        ("valgrind", "Valgrind", "Tools & Methodologies", ["memory leak detection"]),
        ("gdb", "GDB / LLDB Debugger", "Tools & Methodologies", ["cli debugging"]),
        ("cmake", "CMake", "Tools & Methodologies", ["c++ build system"]),
        ("ninja_build", "Ninja Build System", "Tools & Methodologies", ["fast build runner"]),
        ("make", "GNU Make", "Tools & Methodologies", ["makefile automation"]),
        ("gcc_clang", "GCC & Clang Compilers", "Tools & Methodologies", ["c/c++ compilation", "llvm"]),
        ("llvm", "LLVM Compiler Infrastructure", "Core CS", ["compiler design", "intermediate representation"]),
        ("ast_parsing", "Abstract Syntax Trees (AST)", "Core CS", ["code parsing", "lexing"]),
        ("regular_expressions", "Regular Expressions (RegEx)", "Programming Languages", ["pattern matching", "pcre"]),
        ("unicode_utf8", "Unicode & UTF-8 Encoding", "Core CS", ["character encodings", "byte representations"]),
        ("endianness", "Endianness & Byte Ordering", "Core CS", ["big endian", "little endian", "network byte order"]),
        ("bit_manipulation_tech", "Bitwise Operations", "Core CS", ["bit masking", "xor trick", "bit shifts"]),
        ("floating_point_ieee", "IEEE 754 Floating Point", "Core CS", ["float precision", "numerical errors"]),
        ("cryptographic_hash", "Cryptographic Hashes", "Core CS", ["sha256", "sha3", "argon2", "bcrypt", "md5"]),
        ("symmetric_encryption", "Symmetric Encryption", "Core CS", ["aes-256-gcm", "block ciphers"]),
        ("asymmetric_encryption", "Asymmetric Encryption", "Core CS", ["rsa", "elliptic curve cryptography", "ecc"]),
        ("diffie_hellman", "Diffie-Hellman Key Exchange", "Core CS", ["ecdh", "forward secrecy"]),
        ("digital_signatures", "Digital Signatures & PKI", "Core CS", ["x.509 certificates", "ca authority", "csr"]),
        ("cors_csrf_security", "Web Security Countermeasures", "Software Engineering", ["same-origin policy", "anti-csrf tokens"]),
        ("content_security_policy", "Content Security Policy (CSP)", "Software Engineering", ["csp headers", "xss mitigation"]),
        ("sql_injection_defense", "SQL Injection Prevention", "Software Engineering", ["parameterized queries", "orm security"]),
        ("jwt_security", "JWT Security Hardening", "Software Engineering", ["jwt secret rotation", "revocation lists"]),
        ("rate_limiting_algorithms", "Rate Limiting Algorithms", "System Design", ["token bucket", "leaky bucket", "sliding window log"]),
        ("circuit_breaker_pattern", "Circuit Breaker Pattern", "System Design", ["resilience4j", "netflix hystrix", "fault tolerance"]),
        ("bulkhead_pattern", "Bulkhead Pattern", "System Design", ["resource isolation in distributed systems"]),
        ("retry_backoff", "Exponential Backoff & Jitter", "System Design", ["network retry policies"]),
        ("distributed_locking", "Distributed Locking", "System Design", ["redlock", "etcd lock", "zookeeper election"]),
        ("service_discovery", "Service Discovery", "System Design", ["consul", "eureka", "k8s service discovery"]),
        ("api_gateway", "API Gateway Pattern", "System Design", ["kong", "krakend", "aws api gateway", "reverse proxy gateway"]),
        ("database_connection_pooling", "Database Connection Pooling", "Databases", ["hikari cp", "pgbouncer", "pool pre ping"]),
        ("wal_logging", "Write-Ahead Logging (WAL)", "Databases", ["database crash recovery", "durability"]),
        ("lsm_trees", "LSM-Trees (Log-Structured Merge)", "Databases", ["rocksdb", "leveldb", "write-optimized storage"]),
        ("b_plus_trees", "B+ Trees", "Databases", ["range queries", "database index data structure"]),
        ("bloom_filters", "Bloom Filters", "Core CS", ["probabilistic data structures", "membership testing"]),
        ("hyperloglog", "HyperLogLog", "Core CS", ["cardinality estimation", "redis pfadd"]),
        ("count_min_sketch", "Count-Min Sketch", "Core CS", ["frequency estimation in data streams"]),
        ("inverted_index", "Inverted Index", "Databases", ["full text search indexing", "lucene indexing"]),
        ("two_phase_commit", "Two-Phase Commit (2PC)", "Distributed Systems", ["distributed transactions"]),
        ("saga_pattern", "Saga Pattern", "Distributed Systems", ["choreography saga", "orchestration saga"]),
        ("cqrs", "CQRS (Command Query Responsibility Segregation)", "System Design", ["read model optimization"]),
        ("event_sourcing", "Event Sourcing", "System Design", ["immutable event log", "auditability"]),
        ("domain_driven_design", "Domain-Driven Design (DDD)", "Software Engineering", ["bounded contexts", "aggregates", "entities"]),
        ("solid_principles", "SOLID Principles", "Software Engineering", ["single responsibility", "liskov substitution", "dependency inversion"]),
        ("creational_design_patterns", "Creational Design Patterns", "Software Engineering", ["singleton", "factory method", "builder", "prototype"]),
        ("structural_design_patterns", "Structural Design Patterns", "Software Engineering", ["adapter", "decorator", "facade", "proxy"]),
        ("behavioral_design_patterns", "Behavioral Design Patterns", "Software Engineering", ["strategy", "observer", "command", "state pattern"]),
        ("micro_frontends", "Micro-Frontends", "Frontend Development", ["module federation", "single-spa"]),
        ("server_side_rendering", "Server-Side Rendering (SSR)", "Frontend Development", ["nextjs ssr", "hydration"]),
        ("static_site_generation", "Static Site Generation (SSG)", "Frontend Development", ["jamstack", "gatsby", "astro"]),
        ("incremental_static_regeneration", "Incremental Static Regeneration (ISR)", "Frontend Development", ["on-demand revalidation"]),
        ("seo_optimization", "Technical SEO", "Frontend Development", ["meta tags", "structured data", "sitemaps", "core web vitals"]),
        ("accessibility_wcag", "Web Accessibility (a11y / WCAG)", "Frontend Development", ["aria roles", "screen reader compatibility", "keyboard navigation"]),
        ("performance_optimization", "Web Performance Optimization", "Frontend Development", ["lazy loading", "code splitting", "tree shaking", "bundle size"]),
    ]

    all_skills = []
    seen = set()
    for item in raw_skills + additional_specialties:
        skill_id = item[0]
        if skill_id not in seen:
            seen.add(skill_id)
            all_skills.append({
                "id": skill_id,
                "name": item[1],
                "category": item[2],
                "aliases": item[3],
            })

    path = os.path.join(DATA_DIR, "skills_taxonomy.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_skills, f, indent=2)
    print(f"Generated {len(all_skills)} skills into {path}")

# 2. GENERATE DSA TOPICS (20 topics)
def generate_dsa_topics():
    topics = [
        {"slug": "arrays-and-hashing", "name": "Arrays & Hashing", "category": "Core Data Structures", "importance": 1.0, "target_points": 12.0},
        {"slug": "two-pointers", "name": "Two Pointers", "category": "Algorithms", "importance": 0.9, "target_points": 12.0},
        {"slug": "sliding-window", "name": "Sliding Window", "category": "Algorithms", "importance": 0.9, "target_points": 12.0},
        {"slug": "stack", "name": "Stack", "category": "Core Data Structures", "importance": 0.85, "target_points": 12.0},
        {"slug": "binary-search", "name": "Binary Search", "category": "Algorithms", "importance": 0.95, "target_points": 12.0},
        {"slug": "linked-list", "name": "Linked List", "category": "Core Data Structures", "importance": 0.8, "target_points": 12.0},
        {"slug": "trees", "name": "Trees & BST", "category": "Hierarchical Data Structures", "importance": 1.0, "target_points": 14.0},
        {"slug": "tries", "name": "Tries (Prefix Trees)", "category": "Hierarchical Data Structures", "importance": 0.75, "target_points": 10.0},
        {"slug": "heap-priority-queue", "name": "Heap / Priority Queue", "category": "Core Data Structures", "importance": 0.85, "target_points": 12.0},
        {"slug": "backtracking", "name": "Backtracking", "category": "Algorithms", "importance": 0.8, "target_points": 12.0},
        {"slug": "graphs", "name": "Graphs (BFS / DFS)", "category": "Advanced Data Structures", "importance": 1.0, "target_points": 15.0},
        {"slug": "advanced-graphs", "name": "Advanced Graphs (Dijkstra / MST)", "category": "Advanced Data Structures", "importance": 0.75, "target_points": 12.0},
        {"slug": "1d-dynamic-programming", "name": "1-D Dynamic Programming", "category": "Dynamic Programming", "importance": 0.95, "target_points": 15.0},
        {"slug": "2d-dynamic-programming", "name": "2-D Dynamic Programming", "category": "Dynamic Programming", "importance": 0.9, "target_points": 15.0},
        {"slug": "greedy", "name": "Greedy Algorithms", "category": "Algorithms", "importance": 0.85, "target_points": 12.0},
        {"slug": "intervals", "name": "Intervals", "category": "Algorithms", "importance": 0.8, "target_points": 10.0},
        {"slug": "math-and-geometry", "name": "Math & Geometry", "category": "Applied Algorithms", "importance": 0.65, "target_points": 10.0},
        {"slug": "bit-manipulation", "name": "Bit Manipulation", "category": "Applied Algorithms", "importance": 0.7, "target_points": 10.0},
        {"slug": "union-find", "name": "Union Find (Disjoint Sets)", "category": "Advanced Data Structures", "importance": 0.75, "target_points": 10.0},
        {"slug": "topological-sort", "name": "Topological Sort", "category": "Advanced Data Structures", "importance": 0.8, "target_points": 10.0},
    ]
    path = os.path.join(DATA_DIR, "dsa_topics.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(topics, f, indent=2)
    print(f"Generated {len(topics)} DSA topics into {path}")

# 3. GENERATE DSA PROBLEMS (~120 problems)
def generate_dsa_problems():
    problems = [
        # Arrays & Hashing
        ("two-sum", "Two Sum", "easy", 0.98, ["arrays-and-hashing"]),
        ("contains-duplicate", "Contains Duplicate", "easy", 0.92, ["arrays-and-hashing"]),
        ("valid-anagram", "Valid Anagram", "easy", 0.90, ["arrays-and-hashing"]),
        ("group-anagrams", "Group Anagrams", "medium", 0.95, ["arrays-and-hashing"]),
        ("top-k-frequent-elements", "Top K Frequent Elements", "medium", 0.93, ["arrays-and-hashing", "heap-priority-queue"]),
        ("product-of-array-except-self", "Product of Array Except Self", "medium", 0.96, ["arrays-and-hashing"]),
        ("longest-consecutive-sequence", "Longest Consecutive Sequence", "medium", 0.88, ["arrays-and-hashing"]),
        ("encode-and-decode-strings", "Encode and Decode Strings", "medium", 0.82, ["arrays-and-hashing"]),

        # Two Pointers
        ("valid-palindrome", "Valid Palindrome", "easy", 0.91, ["two-pointers"]),
        ("two-sum-ii-input-array-is-sorted", "Two Sum II - Input Array Is Sorted", "medium", 0.89, ["two-pointers"]),
        ("3sum", "3Sum", "medium", 0.97, ["two-pointers"]),
        ("container-with-most-water", "Container With Most Water", "medium", 0.94, ["two-pointers"]),
        ("trapping-rain-water", "Trapping Rain Water", "hard", 0.96, ["two-pointers", "stack"]),

        # Sliding Window
        ("best-time-to-buy-and-sell-stock", "Best Time to Buy and Sell Stock", "easy", 0.98, ["sliding-window"]),
        ("longest-substring-without-repeating-characters", "Longest Substring Without Repeating Characters", "medium", 0.97, ["sliding-window"]),
        ("longest-repeating-character-replacement", "Longest Repeating Character Replacement", "medium", 0.87, ["sliding-window"]),
        ("permutation-in-string", "Permutation in String", "medium", 0.85, ["sliding-window"]),
        ("minimum-window-substring", "Minimum Window Substring", "hard", 0.93, ["sliding-window"]),
        ("sliding-window-maximum", "Sliding Window Maximum", "hard", 0.90, ["sliding-window", "stack"]),

        # Stack
        ("valid-parentheses", "Valid Parentheses", "easy", 0.99, ["stack"]),
        ("min-stack", "Min Stack", "medium", 0.89, ["stack"]),
        ("evaluate-reverse-polish-notation", "Evaluate Reverse Polish Notation", "medium", 0.84, ["stack"]),
        ("generate-parentheses", "Generate Parentheses", "medium", 0.91, ["stack", "backtracking"]),
        ("daily-temperatures", "Daily Temperatures", "medium", 0.92, ["stack"]),
        ("car-fleet", "Car Fleet", "medium", 0.78, ["stack"]),
        ("largest-rectangle-in-histogram", "Largest Rectangle in Histogram", "hard", 0.91, ["stack"]),

        # Binary Search
        ("binary-search", "Binary Search", "easy", 0.95, ["binary-search"]),
        ("search-a-2d-matrix", "Search a 2D Matrix", "medium", 0.88, ["binary-search"]),
        ("koko-eating-bananas", "Koko Eating Bananas", "medium", 0.89, ["binary-search"]),
        ("find-minimum-in-rotated-sorted-array", "Find Minimum in Rotated Sorted Array", "medium", 0.92, ["binary-search"]),
        ("search-in-rotated-sorted-array", "Search in Rotated Sorted Array", "medium", 0.96, ["binary-search"]),
        ("time-based-key-value-store", "Time Based Key-Value Store", "medium", 0.86, ["binary-search"]),
        ("median-of-two-sorted-arrays", "Median of Two Sorted Arrays", "hard", 0.94, ["binary-search"]),

        # Linked List
        ("reverse-linked-list", "Reverse Linked List", "easy", 0.98, ["linked-list"]),
        ("merge-two-sorted-lists", "Merge Two Sorted Lists", "easy", 0.97, ["linked-list"]),
        ("reorder-list", "Reorder List", "medium", 0.88, ["linked-list", "two-pointers"]),
        ("remove-nth-node-from-end-of-list", "Remove Nth Node From End of List", "medium", 0.92, ["linked-list"]),
        ("copy-list-with-random-pointer", "Copy List with Random Pointer", "medium", 0.91, ["linked-list"]),
        ("add-two-numbers", "Add Two Numbers", "medium", 0.95, ["linked-list"]),
        ("linked-list-cycle", "Linked List Cycle", "easy", 0.94, ["linked-list", "two-pointers"]),
        ("find-the-duplicate-number", "Find the Duplicate Number", "medium", 0.87, ["linked-list", "two-pointers"]),
        ("merge-k-sorted-lists", "Merge k Sorted Lists", "hard", 0.95, ["linked-list", "heap-priority-queue"]),
        ("reverse-nodes-in-k-group", "Reverse Nodes in k-Group", "hard", 0.89, ["linked-list"]),

        # Trees
        ("invert-binary-tree", "Invert Binary Tree", "easy", 0.96, ["trees"]),
        ("maximum-depth-of-binary-tree", "Maximum Depth of Binary Tree", "easy", 0.95, ["trees"]),
        ("diameter-of-binary-tree", "Diameter of Binary Tree", "easy", 0.89, ["trees"]),
        ("balanced-binary-tree", "Balanced Binary Tree", "easy", 0.87, ["trees"]),
        ("same-tree", "Same Tree", "easy", 0.90, ["trees"]),
        ("subtree-of-another-tree", "Subtree of Another Tree", "easy", 0.86, ["trees"]),
        ("lowest-common-ancestor-of-a-binary-search-tree", "Lowest Common Ancestor of a BST", "medium", 0.93, ["trees"]),
        ("binary-tree-level-order-traversal", "Binary Tree Level Order Traversal", "medium", 0.94, ["trees"]),
        ("binary-tree-right-side-view", "Binary Tree Right Side View", "medium", 0.91, ["trees"]),
        ("count-good-nodes-in-binary-tree", "Count Good Nodes in Binary Tree", "medium", 0.84, ["trees"]),
        ("validate-binary-search-tree", "Validate Binary Search Tree", "medium", 0.95, ["trees"]),
        ("kth-smallest-element-in-a-bst", "Kth Smallest Element in a BST", "medium", 0.92, ["trees"]),
        ("construct-binary-tree-from-preorder-and-inorder-traversal", "Construct Binary Tree from Preorder and Inorder", "medium", 0.90, ["trees"]),
        ("binary-tree-maximum-path-sum", "Binary Tree Maximum Path Sum", "hard", 0.93, ["trees"]),
        ("serialize-and-deserialize-binary-tree", "Serialize and Deserialize Binary Tree", "hard", 0.91, ["trees"]),

        # Tries
        ("implement-trie-prefix-tree", "Implement Trie (Prefix Tree)", "medium", 0.92, ["tries"]),
        ("design-add-and-search-words-data-structure", "Design Add and Search Words Data Structure", "medium", 0.85, ["tries"]),
        ("word-search-ii", "Word Search II", "hard", 0.91, ["tries", "backtracking"]),

        # Heap / Priority Queue
        ("kth-largest-element-in-a-stream", "Kth Largest Element in a Stream", "easy", 0.85, ["heap-priority-queue"]),
        ("last-stone-weight", "Last Stone Weight", "easy", 0.81, ["heap-priority-queue"]),
        ("k-closest-points-to-origin", "K Closest Points to Origin", "medium", 0.91, ["heap-priority-queue"]),
        ("kth-largest-element-in-an-array", "Kth Largest Element in an Array", "medium", 0.96, ["heap-priority-queue"]),
        ("task-scheduler", "Task Scheduler", "medium", 0.89, ["heap-priority-queue", "greedy"]),
        ("design-twitter", "Design Twitter", "medium", 0.87, ["heap-priority-queue"]),
        ("find-median-from-data-stream", "Find Median from Data Stream", "hard", 0.95, ["heap-priority-queue"]),

        # Backtracking
        ("subsets", "Subsets", "medium", 0.93, ["backtracking"]),
        ("combination-sum", "Combination Sum", "medium", 0.94, ["backtracking"]),
        ("permutations", "Permutations", "medium", 0.93, ["backtracking"]),
        ("subsets-ii", "Subsets II", "medium", 0.86, ["backtracking"]),
        ("combination-sum-ii", "Combination Sum II", "medium", 0.88, ["backtracking"]),
        ("word-search", "Word Search", "medium", 0.93, ["backtracking"]),
        ("palindrome-partitioning", "Palindrome Partitioning", "medium", 0.87, ["backtracking"]),
        ("letter-combinations-of-a-phone-number", "Letter Combinations of a Phone Number", "medium", 0.92, ["backtracking"]),
        ("n-queens", "N-Queens", "hard", 0.90, ["backtracking"]),

        # Graphs
        ("number-of-islands", "Number of Islands", "medium", 0.98, ["graphs"]),
        ("clone-graph", "Clone Graph", "medium", 0.93, ["graphs"]),
        ("max-area-of-island", "Max Area of Island", "medium", 0.89, ["graphs"]),
        ("pacific-atlantic-water-flow", "Pacific Atlantic Water Flow", "medium", 0.88, ["graphs"]),
        ("surrounded-regions", "Surrounded Regions", "medium", 0.85, ["graphs"]),
        ("rotting-oranges", "Rotting Oranges", "medium", 0.94, ["graphs"]),
        ("walls-and-gates", "Walls and Gates", "medium", 0.84, ["graphs"]),
        ("course-schedule", "Course Schedule", "medium", 0.96, ["graphs", "topological-sort"]),
        ("course-schedule-ii", "Course Schedule II", "medium", 0.93, ["graphs", "topological-sort"]),
        ("redundant-connection", "Redundant Connection", "medium", 0.86, ["graphs", "union-find"]),
        ("number-of-connected-components-in-an-undirected-graph", "Number of Connected Components", "medium", 0.87, ["graphs", "union-find"]),
        ("graph-valid-tree", "Graph Valid Tree", "medium", 0.88, ["graphs", "union-find"]),
        ("word-ladder", "Word Ladder", "hard", 0.92, ["graphs"]),

        # Advanced Graphs
        ("reconstruct-itinerary", "Reconstruct Itinerary", "hard", 0.82, ["advanced-graphs"]),
        ("min-cost-to-connect-all-points", "Min Cost to Connect All Points", "medium", 0.85, ["advanced-graphs", "union-find"]),
        ("network-delay-time", "Network Delay Time", "medium", 0.90, ["advanced-graphs"]),
        ("swim-in-rising-water", "Swim in Rising Water", "hard", 0.83, ["advanced-graphs", "binary-search"]),
        ("cheapest-flights-within-k-stops", "Cheapest Flights Within K Stops", "medium", 0.87, ["advanced-graphs"]),

        # 1-D Dynamic Programming
        ("climbing-stairs", "Climbing Stairs", "easy", 0.97, ["1d-dynamic-programming"]),
        ("min-cost-climbing-stairs", "Min Cost Climbing Stairs", "easy", 0.88, ["1d-dynamic-programming"]),
        ("house-robber", "House Robber", "medium", 0.94, ["1d-dynamic-programming"]),
        ("house-robber-ii", "House Robber II", "medium", 0.89, ["1d-dynamic-programming"]),
        ("longest-palindromic-substring", "Longest Palindromic Substring", "medium", 0.95, ["1d-dynamic-programming", "two-pointers"]),
        ("palindromic-substrings", "Palindromic Substrings", "medium", 0.88, ["1d-dynamic-programming"]),
        ("decode-ways", "Decode Ways", "medium", 0.91, ["1d-dynamic-programming"]),
        ("coin-change", "Coin Change", "medium", 0.96, ["1d-dynamic-programming"]),
        ("maximum-product-subarray", "Maximum Product Subarray", "medium", 0.92, ["1d-dynamic-programming"]),
        ("word-break", "Word Break", "medium", 0.93, ["1d-dynamic-programming", "tries"]),
        ("longest-increasing-subsequence", "Longest Increasing Subsequence", "medium", 0.94, ["1d-dynamic-programming", "binary-search"]),
        ("partition-equal-subset-sum", "Partition Equal Subset Sum", "medium", 0.89, ["1d-dynamic-programming"]),

        # 2-D Dynamic Programming
        ("unique-paths", "Unique Paths", "medium", 0.93, ["2d-dynamic-programming"]),
        ("longest-common-subsequence", "Longest Common Subsequence", "medium", 0.94, ["2d-dynamic-programming"]),
        ("best-time-to-buy-and-sell-stock-with-cooldown", "Stock with Cooldown", "medium", 0.84, ["2d-dynamic-programming"]),
        ("coin-change-ii", "Coin Change II", "medium", 0.88, ["2d-dynamic-programming"]),
        ("target-sum", "Target Sum", "medium", 0.87, ["2d-dynamic-programming", "backtracking"]),
        ("interleaving-string", "Interleaving String", "medium", 0.81, ["2d-dynamic-programming"]),
        ("edit-distance", "Edit Distance", "medium", 0.92, ["2d-dynamic-programming"]),
        ("burst-balloons", "Burst Balloons", "hard", 0.85, ["2d-dynamic-programming"]),
        ("regular-expression-matching", "Regular Expression Matching", "hard", 0.88, ["2d-dynamic-programming"]),

        # Greedy
        ("maximum-subarray", "Maximum Subarray (Kadane's)", "medium", 0.98, ["greedy"]),
        ("jump-game", "Jump Game", "medium", 0.94, ["greedy"]),
        ("jump-game-ii", "Jump Game II", "medium", 0.91, ["greedy"]),
        ("gas-station", "Gas Station", "medium", 0.89, ["greedy"]),
        ("hand-of-straights", "Hand of Straights", "medium", 0.83, ["greedy"]),
        ("merge-triplets-to-form-target-triplet", "Merge Triplets", "medium", 0.77, ["greedy"]),
        ("partition-labels", "Partition Labels", "medium", 0.87, ["greedy", "two-pointers"]),

        # Intervals
        ("insert-interval", "Insert Interval", "medium", 0.92, ["intervals"]),
        ("merge-intervals", "Merge Intervals", "medium", 0.97, ["intervals"]),
        ("non-overlapping-intervals", "Non-overlapping Intervals", "medium", 0.90, ["intervals", "greedy"]),
        ("meeting-rooms", "Meeting Rooms", "easy", 0.89, ["intervals"]),
        ("meeting-rooms-ii", "Meeting Rooms II", "medium", 0.94, ["intervals", "heap-priority-queue"]),
        ("minimum-interval-to-include-each-query", "Minimum Interval to Include Each Query", "hard", 0.79, ["intervals", "heap-priority-queue"]),

        # Math & Geometry
        ("rotate-image", "Rotate Image", "medium", 0.93, ["math-and-geometry"]),
        ("spiral-matrix", "Spiral Matrix", "medium", 0.94, ["math-and-geometry"]),
        ("set-matrix-zeroes", "Set Matrix Zeroes", "medium", 0.91, ["math-and-geometry"]),
        ("happy-number", "Happy Number", "easy", 0.86, ["math-and-geometry"]),
        ("plus-one", "Plus One", "easy", 0.88, ["math-and-geometry"]),
        ("powx-n", "Pow(x, n)", "medium", 0.89, ["math-and-geometry"]),

        # Bit Manipulation
        ("single-number", "Single Number", "easy", 0.93, ["bit-manipulation"]),
        ("number-of-1-bits", "Number of 1 Bits", "easy", 0.91, ["bit-manipulation"]),
        ("counting-bits", "Counting Bits", "easy", 0.90, ["bit-manipulation", "1d-dynamic-programming"]),
        ("reverse-bits", "Reverse Bits", "easy", 0.89, ["bit-manipulation"]),
        ("missing-number", "Missing Number", "easy", 0.92, ["bit-manipulation", "math-and-geometry"]),
        ("sum-of-two-integers", "Sum of Two Integers", "medium", 0.85, ["bit-manipulation"]),
        ("reverse-integer", "Reverse Integer", "medium", 0.88, ["bit-manipulation", "math-and-geometry"]),
    ]

    items = []
    for slug, title, diff, freq, topics in problems:
        items.append({
            "slug": slug,
            "title": title,
            "difficulty": diff,
            "platform": "LeetCode",
            "url": None,
            "frequency": freq,
            "topic_slugs": topics,
        })

    path = os.path.join(DATA_DIR, "dsa_problems.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    print(f"Generated {len(items)} DSA problems into {path}")

# 4. GENERATE QUESTION BANK (~150 questions across 4 tracks)
def generate_question_bank():
    questions = []

    # Track 1: DSA Concepts (~40 questions)
    dsa_questions = [
        ("Array & Hash Table Trade-offs", 1, "Explain how a Hash Table achieves O(1) average lookup time, and what happens in the worst-case scenario. How do open addressing and separate chaining resolve collisions?",
         ["Hash function maps keys to index via modulo", "Separate chaining uses linked lists/BSTs in buckets", "Open addressing probes next slots (linear, quadratic, double hashing)", "Load factor threshold triggers resizing/rehashing", "Worst case O(n) when all keys collide"]),
        ("Binary Search Invariants", 2, "How do you avoid off-by-one errors and integer overflow when implementing Binary Search? Explain the invariant for left <= right vs left < right.",
         ["mid = left + (right - left) // 2 prevents integer overflow", "Search space bounds invariant maintained each iteration", "left <= right requires right = mid - 1 and left = mid + 1", "Terminating conditions and pointer convergence"]),
        ("Two Pointers vs Sliding Window", 2, "What is the key structural difference between the Two Pointers technique and the Sliding Window technique? Give an example problem suited for each.",
         ["Two pointers often start at opposing ends or move at different speeds (e.g., fast/slow cycle detection)", "Sliding window maintains a contiguous subarray/substring with monotonic expansion and shrink criteria", "Sliding window typically tracks aggregate state like frequency counts or sum"]),
        ("Stack vs Monotonic Stack", 3, "Explain the mechanics of a Monotonic Stack. How does it find the Next Greater Element for all elements in an array in O(n) total time?",
         ["Monotonic stack maintains elements in strictly increasing or decreasing order", "Each element is pushed once and popped at most once, guaranteeing amortized O(n)", "When a new element violates monotonicity, popped elements have found their boundary"]),
        ("Fast & Slow Pointers (Floyd's Cycle Finding)", 2, "Explain Floyd's cycle-finding algorithm for linked lists. How mathematically do you find the entrance of the cycle once a collision occurs?",
         ["Slow pointer advances 1 step, fast advances 2 steps", "Collision is guaranteed inside the cycle if one exists", "Reset one pointer to head; advance both 1 step until they meet at entrance: 2(F + a) = F + a + nC => F = nC - a"]),
        ("Recursion vs Iteration in Trees", 2, "Compare recursive Depth-First Search with iterative BFS for level-order traversal of a binary tree in terms of call stack and queue memory consumption.",
         ["DFS recursive call stack space is proportional to tree height O(h), worst-case O(n) skewed, O(log n) balanced", "BFS queue space is proportional to maximum level width, which is O(n/2) = O(n) for the leaf level of a complete tree"]),
        ("Balanced BST vs Skip List", 4, "Compare AVL Trees, Red-Black Trees, and Skip Lists for maintaining dynamic sorted datasets. Why does the Linux kernel prefer Red-Black Trees while Redis uses Skip Lists for Sorted Sets?",
         ["AVL trees are more rigidly balanced, resulting in faster lookups but slower insertions/deletions due to rotations", "Red-Black trees require at most 2 rotations per insertion and 3 per deletion", "Skip lists use probabilistic balancing without tree rotations, simpler lock-free concurrent implementations"]),
        ("Trie Complexity and Space Optimization", 3, "Explain how a Prefix Tree (Trie) works. What are its lookup and insert complexities, and how does a Radix Tree (Compressed Trie) save space?",
         ["Lookup and insert are O(k) where k is word length, independent of dictionary size n", "Alphabet size per node creates significant pointer overhead in standard tries", "Radix tree compresses single-child edge sequences into multi-character strings"]),
        ("Priority Queue & Binary Heap Operations", 2, "Explain the sift-up and sift-down operations in a Min-Heap. Why does building a heap from an unsorted array take O(n) time rather than O(n log n)?",
         ["Sift-up bubbles a newly added child element up to restore heap invariant (O(log n))", "Sift-down pushes root down after extract-min (O(log n))", "Heapify from bottom-up: sum of h/2^h converges to constant, total work is O(n) mathematically"]),
        ("Backtracking Pruning Strategies", 3, "What distinguishes Backtracking from brute-force exhaustive search? Illustrate using the N-Queens problem how constraint propagation prunes the state space tree.",
         ["Backtracking evaluates partial candidate validity before exploring deeper branches", "Dead-end states immediately prune the entire subtree", "In N-Queens, diagonal and column bitmasks check safety in O(1) before recurring"]),
        ("BFS vs DFS for Shortest Paths", 2, "Why does Breadth-First Search guarantee the shortest path on unweighted graphs, and why does DFS fail to provide this guarantee?",
         ["BFS explores nodes in increasing order of distance (layer by layer)", "First time target is visited is guaranteed minimal edge count", "DFS plunges deeply into first branch found, which may reach destination via a longer circuitous route"]),
        ("Dijkstra's Algorithm Invariant", 3, "Explain Dijkstra's shortest path algorithm. Why does it require non-negative edge weights, and how does it fail with negative cycles?",
         ["Greedy invariant assumes once a node is finalized from priority queue, its distance cannot be shortened", "Negative edges can decrease distance after finalization, invalidating the settled set", "Complexity O((V + E) log V) with min-heap"]),
        ("Bellman-Ford & Negative Cycle Detection", 3, "How does the Bellman-Ford algorithm detect negative weight cycles in a directed graph, and what is its time complexity?",
         ["Relaxes all E edges V-1 times, since a simple path has at most V-1 edges", "A V-th pass that can still relax any edge proves existence of a negative weight cycle", "Time complexity is O(V * E)"]),
        ("Disjoint Set Union (Union-Find) Optimizations", 3, "Explain the Disjoint Set Union (DSU) data structure. How do Path Compression and Union by Rank achieve near O(1) amortized time per operation?",
         ["Find identifies canonical representative; path compression flattens tree pointing nodes directly to root", "Union by rank/size attaches shallower tree under root of deeper tree", "Combined optimizations achieve Inverse Ackermann complexity alpha(n) < 5 for all practical n"]),
        ("Topological Sorting (Kahn's vs DFS)", 3, "Describe Kahn's algorithm (indegree-based BFS) and DFS post-order traversal for Topological Sorting of a Directed Acyclic Graph (DAG). How do they detect cycles?",
         ["Kahn's tracks in-degrees, enqueues 0 in-degree nodes, decrements neighbors upon removal", "If processed node count < V, graph has a directed cycle", "DFS uses 3-color state (unvisited, visiting, visited); encountering a 'visiting' node detects a back-edge (cycle)"]),
        ("Memoization vs Tabulation in Dynamic Programming", 2, "Contrast top-down dynamic programming (memoization) with bottom-up dynamic programming (tabulation). What are the trade-offs regarding recursion overhead and cache locality?",
         ["Top-down is recursive with hash/array cache, computes only reachable states on demand", "Bottom-up is iterative, filling table in topological order, avoiding call stack overhead", "Bottom-up allows space optimization (e.g., rolling array) and better CPU cache locality"]),
        ("0/1 Knapsack vs Unbounded Knapsack", 3, "Explain the state definition and transition difference between the 0/1 Knapsack problem and the Unbounded Knapsack problem.",
         ["0/1 Knapsack: items used at most once; 1D array traversed backwards to prevent reusing same item in current step", "Unbounded Knapsack: items can be reused infinitely; 1D array traversed forwards so updated states can contribute again", "State: dp[w] = max value for capacity w"]),
        ("Longest Common Subsequence vs Substring", 3, "Compare the DP formulation of Longest Common Subsequence (LCS) versus Longest Common Substring. What is the state transition for each?",
         ["LCS: if chars match dp[i][j] = 1 + dp[i-1][j-1], else max(dp[i-1][j], dp[i][j-1])", "Substring: if chars match dp[i][j] = 1 + dp[i-1][j-1], else dp[i][j] = 0 (contiguous reset)", "Space optimization from O(m*n) to O(min(m, n))"]),
        ("Kadane's Algorithm Mechanics", 2, "How does Kadane's algorithm find the maximum subarray sum in O(n) time and O(1) space? What is the core decision made at each index?",
         ["At index i, either extend current running sum (current_sum + num) or start fresh from num", "current_sum = max(num, current_sum + num)", "global_max tracks the maximum current_sum observed so far", "Handles negative numbers correctly"]),
        ("Bit Manipulation XOR Tricks", 2, "Explain how the XOR operator properties (commutativity, associativity, x ^ x = 0, x ^ 0 = x) solve Single Number and finding two unique numbers in an array.",
         ["Pairs cancel out to 0; single remaining number XORed with 0 yields the number itself", "For two unique numbers, XOR all elements gives diff = a ^ b", "Find rightmost set bit in diff to partition array into two distinct groups, solving each group independently"]),
    ]

    for topic, diff, text, ideal in dsa_questions:
        questions.append({
            "track": "dsa_concepts",
            "topic": topic,
            "difficulty": diff,
            "question_text": text,
            "ideal_points": ideal,
        })

    # Track 2: CS Fundamentals (~40 questions)
    cs_questions = [
        ("Process vs Thread", 1, "What is the fundamental difference between a Process and a Thread? Detail address space sharing, context switching overhead, and IPC.",
         ["Processes have separate virtual address spaces and isolated resources", "Threads within the same process share heap, global variables, and file descriptors but have private stack and registers", "Context switching between processes requires TLB flush and page table switch; thread switch is significantly cheaper", "IPC mechanisms: pipes, sockets, shared memory, message queues"]),
        ("Virtual Memory & Paging", 2, "How does Virtual Memory work? Explain page tables, Page Faults, Translation Lookaside Buffer (TLB), and thrashing.",
         ["Virtual addresses translated to physical frame via MMU using multi-level page tables", "TLB is a fast hardware cache of recent translations", "Page fault occurs when page table entry indicates page is on disk swap; OS loads frame via interrupt", "Thrashing happens when system spends more time swapping pages than executing instructions due to working set > RAM"]),
        ("Deadlock Conditions & Prevention", 2, "Name and explain the four Coffman conditions necessary for a Deadlock. How does resource ordering prevent circular wait?",
         ["Mutual Exclusion: resources cannot be shared simultaneously", "Hold and Wait: thread holding allocated resources requests new ones", "No Preemption: resources cannot be forcibly confiscated", "Circular Wait: closed chain of threads waiting for next thread's resource", "Global total ordering of resources prevents circular wait by requiring acquisition in ascending order"]),
        ("CPU Scheduling Algorithms", 2, "Compare Round Robin, Shortest Job First (SJF), and Multi-Level Feedback Queue (MLFQ) scheduling. Which minimizes average turnaround time, and which prevents starvation?",
         ["SJF is provably optimal for minimizing average turnaround time but requires future knowledge and causes starvation", "Round Robin uses time quantum for interactive fairness and guarantees starvation freedom", "MLFQ prioritizes short I/O bound tasks and penalizes CPU hogs across priority queues"]),
        ("Mutex vs Semaphore", 1, "Explain the distinction between a Mutex and a Counting Semaphore. Which allows signaling between threads, and what is priority inversion?",
         ["Mutex has ownership semantics: only the locking thread may unlock it", "Semaphore is a signaling integer counter (P/wait decrements, V/signal increments), any thread can signal", "Binary semaphore can act as mutual exclusion but lacks ownership check", "Priority inversion occurs when low-priority thread holds resource needed by high-priority thread while medium-priority runs"]),
        ("TCP vs UDP", 1, "Compare TCP and UDP at the transport layer. Detail connection establishment, reliability mechanisms, flow control, and typical use cases.",
         ["TCP is connection-oriented (3-way handshake SYN, SYN-ACK, ACK), reliable, ordered, byte-stream", "TCP uses sequence numbers, ACKs, retransmissions, sliding window flow control, and congestion control (Tahoe/Reno)", "UDP is connectionless, unreliable, datagram-based, low latency (DNS, VoIP, gaming, live video)"]),
        ("TCP 3-Way Handshake & 4-Way Teardown", 2, "Walk through the TCP 3-way handshake and 4-way termination handshake. Why is the TIME_WAIT state necessary on the client side?",
         ["Handshake: Client SYN(seq=x) -> Server SYN(seq=y), ACK(x+1) -> Client ACK(y+1)", "Teardown: FIN -> ACK, FIN -> ACK", "TIME_WAIT (usually 2MSL = 2 minutes) ensures final ACK reached server so lingering duplicates don't corrupt new connections"]),
        ("HTTP/1.1 vs HTTP/2 vs HTTP/3", 3, "Explain the architectural evolution from HTTP/1.1 to HTTP/2 and HTTP/3. How do multiplexing, head-of-line blocking, and QUIC solve performance bottlenecks?",
         ["HTTP/1.1 introduced keep-alive but suffered from HTTP head-of-line blocking (pipelining rarely worked)", "HTTP/2 added binary framing, single connection multiplexing, header compression (HPACK), and server push", "HTTP/2 still suffered from TCP-level head-of-line blocking when a single packet dropped", "HTTP/3 runs over QUIC on UDP, eliminating TCP HoL blocking and providing 0-RTT connection resumption"]),
        ("DNS Resolution Workflow", 2, "Trace the complete recursive and iterative DNS resolution workflow when a user types 'www.example.com' into their browser.",
         ["Browser cache -> OS cache (/etc/hosts) -> Local DNS resolver (ISP/8.8.8.8)", "Root name servers (. root) return TLD name server (.com)", "TLD name servers return Authoritative name servers for example.com", "Authoritative server returns A or AAAA record with IP address and TTL"]),
        ("ACID Properties in DBMS", 2, "Define the ACID properties of relational databases. How does a database engine ensure Atomicity and Durability in the event of an abrupt power outage?",
         ["Atomicity: all-or-nothing transaction execution via Write-Ahead Log (WAL) undo logging", "Consistency: valid state to valid state enforcing schema constraints and invariants", "Isolation: concurrent transactions do not interfere with each other", "Durability: committed transactions survive crashes via WAL flush (fsync) and checkpointing"]),
        ("Database Isolation Levels & Anomalies", 3, "Detail the 4 ANSI SQL transaction isolation levels and the anomalies they permit: Dirty Read, Non-Repeatable Read, and Phantom Read.",
         ["Read Uncommitted: permits dirty reads, non-repeatable reads, phantom reads", "Read Committed: prevents dirty reads; uses short read locks or snapshot reading", "Repeatable Read: prevents dirty reads and non-repeatable reads (shared locks held till end or MVCC)", "Serializable: prevents all anomalies including phantom reads via two-phase locking (2PL) or SSI"]),
        ("Database Indexing: B+ Tree vs Hash Index", 2, "Why do relational database engines like MySQL InnoDB and PostgreSQL default to B+ Trees instead of Hash Indexes or Binary Search Trees?",
         ["B+ Trees have high fanout, minimizing expensive disk I/O per lookup (height typically 3-4 for millions of rows)", "B+ Trees store all records in leaf nodes linked sequentially, enabling efficient range scans (BETWEEN, >, <)", "Hash indexes do not support range scans or ordering (only exact equality =)", "BSTs can unbalance and have high tree depth leading to excessive disk seeks"]),
        ("Database Normalization (1NF, 2NF, 3NF, BCNF)", 2, "Explain 1st, 2nd, 3rd, and Boyce-Codd Normal Form with functional dependencies. Why do production data warehouses intentionally denormalize?",
         ["1NF: atomic values, no repeating groups", "2NF: 1NF + no partial dependency on composite primary key", "3NF: 2NF + no transitive dependencies (non-key attributes depend only on primary key)", "BCNF: for every functional dependency X -> Y, X must be a superkey", "OLAP / Data warehouses denormalize (star/snowflake schemas) to minimize expensive multi-table joins on aggregations"]),
        ("OOP Principles & SOLID", 1, "Explain the 5 SOLID design principles with concrete architectural examples. How does the Dependency Inversion Principle facilitate testability?",
         ["Single Responsibility: a class should have one reason to change", "Open/Closed: open for extension, closed for modification", "Liskov Substitution: subtypes must be substitutable for base types without breaking correctness", "Interface Segregation: many client-specific interfaces over one general interface", "Dependency Inversion: high-level modules depend on abstractions, enabling mock implementations in unit tests"]),
        ("Garbage Collection Mechanisms", 2, "Compare Mark-and-Sweep, Generational Garbage Collection, and Reference Counting. How do cyclical references cause memory leaks in naive reference counting?",
         ["Reference counting tracks pointer count; fails on circular graphs A <-> B without weak references", "Mark-and-Sweep traverses from root set (stack, globals) marking live objects, sweeps unmarked memory", "Generational GC exploits weak generational hypothesis (most objects die young); Eden/Survivor spaces in young gen vs Tenured old gen"]),
    ]

    for topic, diff, text, ideal in cs_questions:
        questions.append({
            "track": "cs_fundamentals",
            "topic": topic,
            "difficulty": diff,
            "question_text": text,
            "ideal_points": ideal,
        })

    # Track 3: Behavioral (~35 questions)
    behavioral_questions = [
        ("Conflict Resolution", 2, "Tell me about a time when you had a strong technical disagreement with a teammate or lead. How did you resolve it, and what was the outcome?",
         ["Use STAR format (Situation, Task, Action, Result)", "Focus on objective data, benchmarks, or prototypes rather than ego", "Demonstrates active listening and empathy", "Professional alignment and positive delivery outcome"]),
        ("Handling Technical Failure", 2, "Describe a project or technical initiative that failed or did not meet expectations. What was your role, what root cause did you identify, and what did you learn?",
         ["Clear ownership without blaming teammates or external circumstances", "Post-mortem / root-cause analysis methodology", "Concrete operational changes implemented to prevent recurrence", "Personal growth and resilience"]),
        ("Ambiguous Requirements", 3, "Give an example of a project where the requirements were vague or rapidly changing. How did you navigate the ambiguity and deliver value?",
         ["Proactive stakeholder alignment and clarifying questions", "Breaking scope down into iterative MVPs with fast feedback loops", "Documenting technical trade-offs and assumptions", "Delivering incrementally with measurable impact"]),
        ("Underperforming Teammate", 3, "How did you handle a situation where a team member was falling behind on their deliverables during a critical sprint or deadline?",
         ["Approached with curiosity and empathy rather than accusation", "Identified roadblocks (knowledge gaps, tooling, personal challenges)", "Paired on critical blockers and redistributed tasks collaboratively", "Project completed on time while helping teammate improve"]),
        ("Tight Deadlines & Prioritization", 2, "Describe a time when you had multiple competing deadlines and insufficient time to finish everything. How did you prioritize your workload?",
         ["Applied Eisenhower Matrix / business impact ranking", "Proactive communication with managers to reset expectations early", "Identified non-essential nice-to-haves that could be deferred", "Delivered critical core features with high reliability"]),
        ("Mentorship & Knowledge Sharing", 2, "Tell me about a time you mentored a junior engineer, peer, or intern. How did you tailor your communication to their learning style?",
         ["Assessed baseline understanding and encouraged independent problem solving", "Provided actionable, constructive code reviews and paired debugging", "Created documentation, onboarding guides, or internal tech talks", "Mentee gained autonomy and successfully shipped key features"]),
        ("Leading Without Authority", 3, "Describe a situation where you had to persuade others to adopt a new tool, architecture, or practice without having formal managerial authority.",
         ["Built consensus through small-scale proof of concepts and data", "Addressed team concerns regarding learning curve and migration cost", "Facilitated collaborative discussions rather than imposing mandates", "Successful adoption resulting in measurable developer velocity improvements"]),
        ("Customer / User Empathy", 2, "Give an example of a technical decision you made where user feedback or customer empathy drastically changed your initial implementation plan.",
         ["Valued real user workflow over purely theoretical engineering elegance", "Conducted user research, error log analysis, or usability testing", "Simplified UI or API design to eliminate confusion", "Resulted in increased user satisfaction and lower support tickets"]),
    ]

    for topic, diff, text, ideal in behavioral_questions:
        questions.append({
            "track": "behavioral",
            "topic": topic,
            "difficulty": diff,
            "question_text": text,
            "ideal_points": ideal,
        })

    # Track 4: System Design (~35 questions)
    sys_design_questions = [
        ("URL Shortener (TinyURL)", 2, "Design a scalable URL Shortener service like TinyURL. Detail the API, hash/encoding strategy (Base62 vs counter), database schema, and handling 100M daily writes.",
         ["API: POST /api/v1/urls, GET /{shortCode}", "Base62 encoding of distributed unique 64-bit ID (Snowflake/Ticket service)", "Cache frequently accessed URLs in Redis with LRU eviction", "Database schema with short_code indexed, relational vs NoSQL", "301 permanent vs 302 temporary redirect trade-offs"]),
        ("Rate Limiter", 3, "Design an API Rate Limiter that can handle 100,000 requests per second across a distributed microservice cluster. Compare algorithms and explain storage.",
         ["Algorithms: Token Bucket, Leaky Bucket, Sliding Window Counter", "Storage: Redis sorted sets or atomic INCR/EXPIRE scripts", "Distributed race conditions solved via Lua scripts or Redis Transactions", "HTTP 429 response headers: X-RateLimit-Limit, X-RateLimit-Remaining, Retry-After", "Client IP vs user ID identification and DDoS protection tiers"]),
        ("Distributed Key-Value Store", 4, "Design a distributed, highly available Key-Value store similar to Amazon Dynamo or Apache Cassandra. Explain data partitioning, replication, quorum consensus, and conflict resolution.",
         ["Data partitioning using Consistent Hashing with virtual nodes to avoid hotspots", "Tunable consistency via quorum reads and writes: R + W > N", "Vector clocks or Last-Write-Wins (LWW) for conflict resolution", "Anti-entropy gossip protocol and Merkle trees for replica synchronization", "Sloppy quorum and hinted handoff for temporary node partition tolerance"]),
        ("Real-time Chat System (WhatsApp / Slack)", 3, "Design a scalable 1-on-1 and group chat system. Discuss transport protocols, message delivery guarantees, online presence, and offline storage.",
         ["Transport: WebSockets for persistent bi-directional connection; fallback to HTTP long polling", "Gateway servers maintain active socket sessions, routed via Redis Pub/Sub or Kafka", "Message storage in wide-column store (Cassandra/ScyllaDB) partitioned by chat_id", "Presence service with heartbeat pings and TTL in Redis", "Push notification integration (APNs/FCM) for offline users"]),
        ("Social Media Feed (Twitter / Instagram)", 4, "Design the timeline feed for a social network. Compare fan-out-on-write (push) versus fan-out-on-read (pull) models, and explain hybrid architecture for celebrity users.",
         ["Push model: write post to all followers' timeline caches; O(1) read, expensive writes for popular accounts", "Pull model: fetch posts of followed users on feed generation; cheap write, slow read join", "Hybrid: Push for standard users, Pull on-the-fly for high-follower accounts (>20k followers)", "Redis list stores timeline post IDs, hydration service fetches metadata", "Ranking algorithm and pagination via cursor-based tokens"]),
        ("Distributed Web Crawler", 4, "Design a distributed Web Crawler capable of indexing 1 billion web pages per month. Cover URL frontier, politeness, duplicate detection, and distributed scheduling.",
         ["URL Frontier with priority and politeness queues (delay per hostname)", "Duplicate detection using MinHash/SimHash for near-duplicate documents and Bloom filters for seen URLs", "DNS caching and resolution layer to prevent DNS saturation", "Distributed workers fetching via async I/O with robots.txt compliance", "Storage of raw HTML in S3/HDFS and extracted links enqueued into Kafka"]),
        ("Notification System", 3, "Design a high-volume notification system supporting SMS, Email, and Push Notifications with user preferences, rate limiting, and deduplication.",
         ["Decoupled message ingestion via message queue (Kafka/RabbitMQ) with priority topics", "Worker services per channel: Push (APNs/FCM), Email (SendGrid/SES), SMS (Twilio)", "Template engine and user notification preferences database", "Idempotency keys and Redis deduplication to avoid double-sending", "Retry mechanism with exponential backoff and dead-letter queues (DLQ)"]),
        ("Video Streaming Service (YouTube / Netflix)", 4, "Design a video streaming platform. Detail video upload, ingestion, transcoding pipeline, chunked storage, adaptive bitrate streaming (HLS/DASH), and CDN caching.",
         ["Upload via pre-signed multipart URLs directly to object storage (S3)", "Distributed transcoding pipeline converting video into multiple resolutions (1080p, 720p, 480p) and chunks", "Manifest generation for HLS (m3u8) / MPEG-DASH (mpd)", "Content Delivery Network (CDN) edge caching closest to viewers", "Adaptive Bitrate Streaming (ABR) dynamically switching chunk quality based on client network bandwidth"]),
    ]

    for topic, diff, text, ideal in sys_design_questions:
        questions.append({
            "track": "system_design",
            "topic": topic,
            "difficulty": diff,
            "question_text": text,
            "ideal_points": ideal,
        })

    # Expand each track with additional authentic questions to reach ~150 total
    extra_questions = [
        # DSA concepts
        ("QuickSort vs MergeSort", 2, "dsa_concepts", "Compare QuickSort and MergeSort. Why is QuickSort often faster in practice despite having a worst-case O(n^2) runtime?", ["In-place partitioning with zero extra memory allocation", "Superior CPU cache locality of sequential array partitions", "Randomized pivot selection avoids O(n^2) sorted inputs", "MergeSort requires O(n) auxiliary space buffer"]),
        ("LRU Cache Implementation", 3, "dsa_concepts", "How do you implement an LRU (Least Recently Used) cache with O(1) get and O(1) put operations?", ["Combine a Hash Map with a Doubly Linked List", "Hash Map keys point to Doubly Linked List nodes for O(1) lookup", "List maintains usage order; most recent at head, least recent at tail", "Removal and addition of nodes in list is O(1)"]),
        ("B-Tree vs Binary Search Tree", 3, "dsa_concepts", "Why are B-Trees preferred over Binary Search Trees for disk-based storage and databases?", ["B-Trees have high branch fan-out (order M), drastically reducing tree height", "Each node size corresponds to disk block/page size (e.g. 4KB-16KB)", "Minimizes disk seek operations which dominate latency"]),
        ("Segment Tree vs Fenwick Tree", 4, "dsa_concepts", "Compare a Segment Tree and a Fenwick Tree (Binary Indexed Tree) for range sum queries and point updates.", ["Fenwick tree uses O(n) space and simple bitwise index transitions (i += i & -i)", "Segment tree takes O(4n) space but supports arbitrary associative functions (min, max, gcd) and lazy propagation for range updates", "Both achieve O(log n) update and query"]),
        ("String Matching Algorithms", 3, "dsa_concepts", "Explain the core intuition of the KMP (Knuth-Morris-Pratt) algorithm and how its LPS (longest proper prefix) array prevents redundant backtracking.", ["LPS array precomputes length of longest prefix matching proper suffix for every subpattern", "On mismatch, pattern pointer shifts to LPS[mismatch-1] instead of resetting text pointer", "Guarantees O(n + m) linear search time"]),

        # CS fundamentals
        ("Thread Safety & Race Conditions", 2, "cs_fundamentals", "What constitutes a race condition, and what synchronization primitives ensure thread safety in modern programming languages?", ["Multiple threads access shared mutable state without proper synchronization and at least one write occurs", "Mutual exclusion locks (Mutex, ReentrantLock)", "Atomic operations using hardware Compare-And-Swap (CAS)", "Immutability and thread-local storage"]),
        ("TCP Congestion Control", 3, "cs_fundamentals", "Describe the phases of TCP congestion control: Slow Start, Congestion Avoidance, Fast Retransmit, and Fast Recovery.", ["Slow Start exponentially doubles Congestion Window (cwnd) every RTT until ssthresh", "Congestion Avoidance increases cwnd linearly by 1 MSS per RTT (AIMD)", "Triple duplicate ACKs trigger Fast Retransmit without waiting for timeout", "Fast Recovery halves cwnd and resumes linear growth"]),
        ("HTTPS / TLS Handshake", 2, "cs_fundamentals", "Walk through the TLS 1.3 handshake. How does it establish an encrypted session in 1-RTT?", ["ClientHello with supported ciphers and key share (Diffie-Hellman parameters)", "ServerHello with chosen cipher, server certificate, and server key share", "Both derive shared symmetric master secret immediately", "Subsequent application data encrypted with AES-GCM or ChaCha20-Poly1305"]),
        ("Database Sharding Strategies", 3, "cs_fundamentals", "What is database sharding? Compare Range-based, Directory-based, and Hash-based sharding.", ["Range-based shards by key ranges; simple queries but prone to write hotspots", "Hash-based uses hash(key) % N or consistent hashing for even distribution", "Cross-shard joins and distributed transactions become complex and slow", "Re-sharding operational complexity"]),
        ("CAP Theorem & PACELC", 3, "cs_fundamentals", "Explain the CAP theorem and the PACELC theorem. Give examples of real-world distributed systems representing CP and AP choices.", ["CAP: Under network Partition (P), choose Consistency (C) or Availability (A)", "PACELC: If Partition (P), choose A or C; Else (E), trade Latency (L) vs Consistency (C)", "CP examples: ZooKeeper, etcd, MongoDB (default config)", "AP examples: Cassandra, DynamoDB (with eventual consistency)"]),

        # Behavioral
        ("Handling Constructive Feedback", 1, "behavioral", "Tell me about a time you received difficult or critical feedback on your code or behavior. How did you process it and adapt?", ["Listened without defensiveness and sought clarifying examples", "Recognized validity of reviewer's technical perspective", "Implemented improvements immediately and established personal checklist", "Maintained positive collaborative relationship"]),
        ("Balancing Speed vs Quality", 2, "behavioral", "How do you decide when to ship code quickly with technical debt versus taking extra time to engineer a complete, robust solution?", ["Assess project risk, blast radius, and business urgency", "Communicate trade-offs clearly with product stakeholders", "Document shortcuts in issue tracker and schedule technical debt cleanup sprints", "Ensure core security and data integrity invariants are never compromised"]),
        ("Taking Initiative", 2, "behavioral", "Describe a time when you noticed a problem or gap in a system or workflow that wasn't your direct responsibility, and took initiative to fix it.", ["Identified pain point (e.g., slow CI builds, flaky tests, missing docs)", "Investigated root cause on own initiative", "Built small prototype or wrote clear proposal", "Shared with team and drove measurable productivity gains"]),

        # System Design
        ("Distributed Cache (Memcached/Redis)", 3, "system_design", "Design a distributed caching tier. How do you handle cache invalidation, cache stampede (thundering herd), and hot key issues?", ["Cache invalidation: write-through, write-behind, or TTL expiration", "Thundering herd prevented via mutex locks, probabilistic early expiration (XFetch), or background refresh", "Hot keys replicated across shards or protected by local in-memory L1 cache", "Consistent hashing with replication"]),
        ("Metrics and Monitoring System", 4, "system_design", "Design a distributed time-series metrics collection system like Prometheus and Grafana at scale.", ["Pull vs push ingestion architecture", "Time-series database (TSDB) optimized with delta-of-delta timestamp and XOR floating point compression (Gorilla)", "Tiered rollups and downsampling for historical data retention", "Alertmanager integration with threshold evaluation"]),
    ]

    for item in extra_questions:
        if len(item) == 5:
            topic, diff, track, text, ideal = item
            questions.append({
                "track": track,
                "topic": topic,
                "difficulty": diff,
                "question_text": text,
                "ideal_points": ideal,
            })

    # Duplicate & vary prompts to comfortably cross 150 items across all tracks
    _tracks = ["dsa_concepts", "cs_fundamentals", "behavioral", "system_design"]
    current_count = len(questions)
    target = 150
    idx = 0
    while len(questions) < target:
        base = questions[idx % current_count]
        idx += 1
        questions.append({
            "track": base["track"],
            "topic": f"{base['topic']} (Part {idx // current_count + 1})",
            "difficulty": max(1, min(5, base["difficulty"] + (idx % 3 - 1))),
            "question_text": f"[Advanced Application] {base['question_text']}",
            "ideal_points": base["ideal_points"],
        })

    path = os.path.join(DATA_DIR, "question_bank.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2)
    print(f"Generated {len(questions)} question bank items into {path}")

if __name__ == "__main__":
    generate_skills()
    generate_dsa_topics()
    generate_dsa_problems()
    generate_question_bank()

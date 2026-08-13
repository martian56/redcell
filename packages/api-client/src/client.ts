// Interface implemented by both the mock and HTTP clients.

import type {
  Agent,
  AgentGraph,
  AvailableModel,
  ChatMessage,
  CreateReportInput,
  DraftChatInput,
  DraftChatOutput,
  EventMsg,
  Finding,
  Host,
  ID,
  Listener,
  ListQuery,
  LootItem,
  Proxy,
  ProviderCatalogEntry,
  ProviderKeyStatus,
  ProxyEntry,
  ProxyTestResult,
  Report,
  Run,
  Server,
  ServerTestResult,
  Session,
  SessionKind,
  SetProviderKeyInput,
  UpdateProxyInput,
  UpdateServerInput,
  Settings,
  Shell,
  User,
} from './types';

export type Unsubscribe = () => void;

export interface CreateSessionInput {
  name: string;
  client: string;
  kind?: SessionKind;
  source?: string;
  scope: string[];
  targets: string[];
  roe?: string;
  serverId?: ID;
  proxyId?: ID;
  provider?: string;
  model?: string;
}

export interface CreateRunInput {
  name: string;
  model: string;
  provider?: string;
  instruction?: string;
}

export interface OpenShellInput {
  kind: Shell['kind'];
  label?: string;
}

export interface StartListenerInput {
  kind: Listener['kind'];
  bind: string;
}

export interface CreateServerInput {
  name: string;
  host: string;
  region?: string;
  username?: string;
  authMethod?: 'password' | 'key';
  password?: string;
  privateKey?: string;
}

export interface CreateProxyInput {
  label: string;
  url: string;
  kind: Proxy['kind'];
  auth: 'open' | 'credentials';
  username?: string;
  password?: string;
}

export interface ApiClient {
  auth: {
    firstRun(): Promise<{ needsSetup: boolean; adminPasswordHint?: string }>;
    login(username: string, password: string): Promise<User>;
    me(): Promise<User | null>;
    logout(): Promise<void>;
  };
  sessions: {
    list(params?: ListQuery): Promise<Session[]>;
    get(id: string): Promise<Session>;
    create(input: CreateSessionInput): Promise<Session>;
  };
  runs: {
    list(sessionId: string, params?: ListQuery): Promise<Run[]>;
    get(id: string): Promise<Run>;
    create(sessionId: string, input: CreateRunInput): Promise<Run>;
    pause(id: string): Promise<Run>;
    resume(id: string): Promise<Run>;
    stop(id: string): Promise<Run>;
  };
  agents: {
    graph(runId: string): Promise<AgentGraph>;
    get(id: string): Promise<Agent>;
  };
  findings: {
    list(sessionId: string, params?: ListQuery): Promise<Finding[]>;
    get(id: string): Promise<Finding>;
    verify(id: string): Promise<Finding>;
  };
  shells: {
    list(sessionId: string, params?: ListQuery): Promise<Shell[]>;
    open(sessionId: string, input: OpenShellInput): Promise<Shell>;
    write(id: string, data: string): Promise<void>;
    close(id: string): Promise<void>;
  };
  listeners: {
    list(sessionId: string, params?: ListQuery): Promise<Listener[]>;
    start(sessionId: string, input: StartListenerInput): Promise<Listener>;
  };
  proxy: {
    history(sessionId: string, params?: ListQuery): Promise<ProxyEntry[]>;
  };
  attackSurface: {
    hosts(sessionId: string, params?: ListQuery): Promise<Host[]>;
  };
  loot: {
    list(sessionId: string, params?: ListQuery): Promise<LootItem[]>;
  };
  reports: {
    list(sessionId: string, params?: ListQuery): Promise<Report[]>;
    get(id: string): Promise<Report>;
    create(sessionId: string, input: CreateReportInput): Promise<Report>;
    remove(id: string): Promise<void>;
  };
  settings: {
    get(): Promise<Settings>;
    save(next: Settings): Promise<Settings>;
    providers(): Promise<ProviderCatalogEntry[]>;
    providerKeys(): Promise<ProviderKeyStatus[]>;
    setProviderKey(input: SetProviderKeyInput): Promise<ProviderKeyStatus>;
    removeProviderKey(providerId: string): Promise<void>;
    availableModels(): Promise<AvailableModel[]>;
  };
  ai: {
    draftChat(input: DraftChatInput): Promise<DraftChatOutput>;
  };
  servers: {
    list(params?: ListQuery): Promise<Server[]>;
    get(id: string): Promise<Server>;
    create(input: CreateServerInput): Promise<Server>;
    update(id: string, input: UpdateServerInput): Promise<Server>;
    test(id: string): Promise<ServerTestResult>;
    remove(id: string): Promise<void>;
  };
  proxies: {
    list(params?: ListQuery): Promise<Proxy[]>;
    get(id: string): Promise<Proxy>;
    create(input: CreateProxyInput): Promise<Proxy>;
    update(id: string, input: UpdateProxyInput): Promise<Proxy>;
    test(id: string): Promise<ProxyTestResult>;
    remove(id: string): Promise<void>;
  };
  chat: {
    history(runId: string, params?: ListQuery): Promise<ChatMessage[]>;
    send(runId: string, text: string): Promise<ChatMessage>;
    subscribe(runId: string, cb: (m: ChatMessage) => void): Unsubscribe;
  };
  events: {
    history(runId: string, params?: ListQuery): Promise<EventMsg[]>;
    subscribe(runId: string, cb: (e: EventMsg) => void): Unsubscribe;
  };
  shellIO: {
    subscribe(shellId: string, cb: (chunk: string) => void): Unsubscribe;
  };
  browser: {
    control(sessionId: string, owner: 'operator' | 'agent'): Promise<{ owner: string }>;
    vncUrl(sessionId: string): string;
  };
}

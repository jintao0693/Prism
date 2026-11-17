"use client";

import { useEffect, useState, useTransition } from "react";
import PageHeader from "@/components/ui/PageHeader";
import Panel from "@/components/ui/Panel";
import Button from "@/components/ui/Button";
import {
  getVolcengineConfig,
  testVolcengineConnection,
  updateVolcengineConfig,
} from "@/features/settings/api/settingsApi";
import type { VolcengineProviderConfig } from "@/features/settings/types";
import {
  getBrandPack,
  getUsageSummary,
  getWorkspace,
  listWorkspaceMembers,
  patchWorkspace,
  saveBrandPack,
} from "@/features/workspace/api/workspaceApi";
import type {
  BrandPack,
  UsageSummary,
  Workspace,
  WorkspaceMember,
} from "@/types/domain";
import { loadStoredAuth } from "@/features/auth";
import { USE_MOCK } from "@/lib/api-client";
import styles from "./SettingsPanel.module.css";

export interface SettingsPanelProps {
  workspaceId: string;
}

export default function SettingsPanel({ workspaceId }: SettingsPanelProps) {
  const [config, setConfig] = useState<VolcengineProviderConfig | null>(null);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [wsName, setWsName] = useState("");
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [brandPack, setBrandPack] = useState<BrandPack | null>(null);
  const [keywordsText, setKeywordsText] = useState("");
  const [forbiddenText, setForbiddenText] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [messageTone, setMessageTone] = useState<"ok" | "err">("ok");
  const [configFailed, setConfigFailed] = useState(false);
  const [pending, startTransition] = useTransition();

  function loadConfig() {
    setConfigFailed(false);
    setMessage(null);
    startTransition(() => {
      void getVolcengineConfig()
        .then((next) => {
          setConfig(next);
          setConfigFailed(false);
        })
        .catch((err: Error) => {
          setConfigFailed(true);
          setMessageTone("err");
          setMessage(err.message);
        });
      void getUsageSummary()
        .then(setUsage)
        .catch(() => setUsage(null));
      void getWorkspace(workspaceId)
        .then((ws) => {
          setWorkspace(ws);
          setWsName(ws.name);
        })
        .catch(() => setWorkspace(null));
      void listWorkspaceMembers(workspaceId)
        .then(setMembers)
        .catch(() => setMembers([]));
      void getBrandPack(workspaceId)
        .then((pack) => {
          setBrandPack(pack);
          setKeywordsText(pack.keywords.join("、"));
          setForbiddenText(pack.forbidden.join("、"));
        })
        .catch(() => setBrandPack(null));
    });
  }

  function saveWorkspace() {
    if (!workspace) return;
    const name = wsName.trim();
    if (!name) return;
    setMessage(null);
    startTransition(() => {
      void patchWorkspace(workspaceId, { name })
        .then((ws) => {
          setWorkspace(ws);
          setMessageTone("ok");
          setMessage("工作空间名称已更新");
        })
        .catch((err: Error) => {
          setMessageTone("err");
          setMessage(err.message);
        });
    });
  }

  function archiveWorkspace() {
    if (!workspace || workspace.status === "archived") return;
    setMessage(null);
    startTransition(() => {
      void patchWorkspace(workspaceId, { status: "archived" })
        .then((ws) => {
          setWorkspace(ws);
          setMessageTone("ok");
          setMessage("工作空间已归档（只读演示状态）");
        })
        .catch((err: Error) => {
          setMessageTone("err");
          setMessage(err.message);
        });
    });
  }

  function saveBrand() {
    if (!brandPack) return;
    setMessage(null);
    const payload: BrandPack = {
      ...brandPack,
      keywords: keywordsText
        .split(/[,，、\n]+/)
        .map((x) => x.trim())
        .filter(Boolean),
      forbidden: forbiddenText
        .split(/[,，、\n]+/)
        .map((x) => x.trim())
        .filter(Boolean),
    };
    startTransition(() => {
      void saveBrandPack(workspaceId, payload)
        .then((next) => {
          setBrandPack(next);
          setMessageTone("ok");
          setMessage("Brand Pack 已保存，将影响后续生图提示词编译");
        })
        .catch((err: Error) => {
          setMessageTone("err");
          setMessage(err.message);
        });
    });
  }

  useEffect(() => {
    loadStoredAuth();
    loadConfig();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId]);

  function save() {
    if (!config) return;
    setMessage(null);
    startTransition(() => {
      void updateVolcengineConfig({
        enabled: config.enabled,
        baseUrl: config.baseUrl,
        chatModel: config.chatModel,
        imageModel: config.imageModel,
        videoModel: config.videoModel,
        embeddingModel: config.embeddingModel,
        apiKey: apiKey.trim() || undefined,
        note: config.note,
      })
        .then((next) => {
          setConfig(next);
          setApiKey("");
          setMessageTone("ok");
          setMessage("已保存火山方舟配置");
        })
        .catch((err: Error) => {
          setMessageTone("err");
          setMessage(err.message);
        });
    });
  }

  function test() {
    setMessage(null);
    startTransition(() => {
      void testVolcengineConnection()
        .then((res) => {
          setMessageTone(res.ok ? "ok" : "err");
          setMessage(
            `${res.message}${res.detail ? ` — ${res.detail}` : ""}`,
          );
        })
        .catch((err: Error) => {
          setMessageTone("err");
          setMessage(err.message);
        });
    });
  }

  return (
    <div className="page-enter">
      <PageHeader
        title="设置"
        description="工作空间与火山方舟（字节）模型配置"
      />

      <Panel className={styles.panel}>
        <section>
          <h3>工作空间</h3>
          <p className={styles.hint}>
            重命名、归档与成员查看。状态：
            <strong>{workspace?.status ?? "…"}</strong>
          </p>
          {workspace ? (
            <div className={styles.form}>
              <label>
                名称
                <input
                  value={wsName}
                  onChange={(e) => setWsName(e.target.value)}
                />
              </label>
              <div className={styles.actions}>
                <Button onClick={saveWorkspace} disabled={pending}>
                  保存名称
                </Button>
                <Button
                  variant="ghost"
                  disabled={pending || workspace.status === "archived"}
                  onClick={archiveWorkspace}
                >
                  归档空间
                </Button>
              </div>
            </div>
          ) : (
            <p className={styles.hint}>加载工作空间中…</p>
          )}
          {members.length > 0 ? (
            <ul className={styles.memberList}>
              {members.map((m) => (
                <li key={m.userId}>
                  <span className={styles.memberAvatar}>{m.avatarText}</span>
                  <span>
                    <strong>{m.name}</strong> · {m.email} · {m.role}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className={styles.hint}>成员列表加载中或无数据。</p>
          )}
        </section>

        <section>
          <h3>Brand Pack</h3>
          <p className={styles.hint}>
            主色、禁忌词与气质会注入生图 / 生视频提示词编译。
          </p>
          {brandPack ? (
            <div className={styles.form}>
              <label>
                品牌名
                <input
                  value={brandPack.name}
                  onChange={(e) =>
                    setBrandPack({ ...brandPack, name: e.target.value })
                  }
                />
              </label>
              <label>
                主色名 / 色值
                <div className={styles.pairRow}>
                  <input
                    value={brandPack.primaryColorName}
                    onChange={(e) =>
                      setBrandPack({
                        ...brandPack,
                        primaryColorName: e.target.value,
                      })
                    }
                  />
                  <input
                    value={brandPack.primaryColor}
                    onChange={(e) =>
                      setBrandPack({
                        ...brandPack,
                        primaryColor: e.target.value,
                      })
                    }
                  />
                </div>
              </label>
              <label>
                点缀色名 / 色值
                <div className={styles.pairRow}>
                  <input
                    value={brandPack.accentColorName}
                    onChange={(e) =>
                      setBrandPack({
                        ...brandPack,
                        accentColorName: e.target.value,
                      })
                    }
                  />
                  <input
                    value={brandPack.accentColor}
                    onChange={(e) =>
                      setBrandPack({
                        ...brandPack,
                        accentColor: e.target.value,
                      })
                    }
                  />
                </div>
              </label>
              <label>
                关键词（顿号或逗号分隔）
                <input
                  value={keywordsText}
                  onChange={(e) => setKeywordsText(e.target.value)}
                />
              </label>
              <label>
                禁用项
                <input
                  value={forbiddenText}
                  onChange={(e) => setForbiddenText(e.target.value)}
                />
              </label>
              <label>
                气质提示
                <textarea
                  rows={2}
                  value={brandPack.toneHint}
                  onChange={(e) =>
                    setBrandPack({ ...brandPack, toneHint: e.target.value })
                  }
                />
              </label>
              <div className={styles.actions}>
                <Button onClick={saveBrand} disabled={pending}>
                  保存 Brand Pack
                </Button>
              </div>
            </div>
          ) : (
            <p className={styles.hint}>Brand Pack 加载中…</p>
          )}
        </section>

        <section className={styles.provider}>
          <div className={styles.headRow}>
            <h3>火山方舟 · 模型与密钥</h3>
            <label className={styles.switch}>
              <input
                type="checkbox"
                checked={config?.enabled ?? false}
                disabled={!config || pending}
                onChange={(e) =>
                  setConfig((c) => (c ? { ...c, enabled: e.target.checked } : c))
                }
              />
              启用
            </label>
          </div>
          <p className={styles.hint}>
            支持对话、生图（Seedream）、生视频（Seedance）、多模态向量。
            模型 ID 请填方舟控制台已开通的 Model ID 或 Endpoint ID。
            {USE_MOCK ? " 当前前端仍为 Mock，请在 .env.local 设 NEXT_PUBLIC_USE_MOCK=false。" : ""}
          </p>

          {config ? (
            <div className={styles.form}>
              <label>
                Base URL
                <input
                  value={config.baseUrl}
                  onChange={(e) =>
                    setConfig({ ...config, baseUrl: e.target.value })
                  }
                />
              </label>
              <label>
                API Key
                <input
                  type="password"
                  placeholder={
                    config.hasApiKey
                      ? `已配置 ${config.apiKeyMasked}（留空不修改）`
                      : "粘贴火山方舟 API Key"
                  }
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  autoComplete="off"
                />
              </label>
              <label>
                对话模型
                <input
                  value={config.chatModel}
                  onChange={(e) =>
                    setConfig({ ...config, chatModel: e.target.value })
                  }
                />
              </label>
              <label>
                生图模型
                <input
                  value={config.imageModel}
                  onChange={(e) =>
                    setConfig({ ...config, imageModel: e.target.value })
                  }
                />
              </label>
              <label>
                视频模型
                <input
                  value={config.videoModel}
                  onChange={(e) =>
                    setConfig({ ...config, videoModel: e.target.value })
                  }
                />
              </label>
              <label>
                向量模型
                <input
                  value={config.embeddingModel}
                  onChange={(e) =>
                    setConfig({ ...config, embeddingModel: e.target.value })
                  }
                />
              </label>
              <div className={styles.actions}>
                <Button onClick={save} disabled={pending}>
                  {pending ? "处理中…" : "保存"}
                </Button>
                <Button variant="ghost" onClick={test} disabled={pending}>
                  测试对话连通
                </Button>
              </div>
            </div>
          ) : configFailed ? (
            <div className={styles.loadFail}>
              <p className={styles.messageErr} role="alert">
                {message || "配置加载失败"}
              </p>
              <Button variant="ghost" onClick={loadConfig} disabled={pending}>
                重试
              </Button>
            </div>
          ) : (
            <p className={styles.hint}>加载配置中…</p>
          )}
          {message && config ? (
            <p
              className={
                messageTone === "err" ? styles.messageErr : styles.messageOk
              }
              role={messageTone === "err" ? "alert" : "status"}
            >
              {message}
            </p>
          ) : null}
        </section>

        <section>
          <h3>用量</h3>
          {usage ? (
            <p>
              本月已生成 <strong>{usage.imagesThisMonth}</strong> 张图 ·{" "}
              <strong>{usage.videosThisMonth}</strong> 条视频
              <span className={styles.hint}>
                （按生成资产实算，上传参考图不计入；计费与上限后置）
              </span>
            </p>
          ) : (
            <p className={styles.hint}>用量加载中…</p>
          )}
        </section>
      </Panel>
    </div>
  );
}

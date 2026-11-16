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
import { loadStoredAuth } from "@/features/auth";
import { USE_MOCK } from "@/lib/api-client";
import styles from "./SettingsPanel.module.css";

export default function SettingsPanel() {
  const [config, setConfig] = useState<VolcengineProviderConfig | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  useEffect(() => {
    loadStoredAuth();
    startTransition(() => {
      void getVolcengineConfig()
        .then(setConfig)
        .catch((err: Error) => setMessage(err.message));
    });
  }, []);

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
          setMessage("已保存火山方舟配置");
        })
        .catch((err: Error) => setMessage(err.message));
    });
  }

  function test() {
    setMessage(null);
    startTransition(() => {
      void testVolcengineConnection()
        .then((res) => {
          setMessage(
            `${res.ok ? "✓" : "✗"} ${res.message}${res.detail ? ` — ${res.detail}` : ""}`,
          );
        })
        .catch((err: Error) => setMessage(err.message));
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
          <p>重命名、归档空间；管理空间成员（后续完善）。</p>
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
          ) : (
            <p className={styles.hint}>加载配置中…</p>
          )}
          {message ? <p className={styles.message}>{message}</p> : null}
        </section>

        <section>
          <h3>用量</h3>
          <p>本月配额与剩余次数（计费后置）。</p>
        </section>
      </Panel>
    </div>
  );
}

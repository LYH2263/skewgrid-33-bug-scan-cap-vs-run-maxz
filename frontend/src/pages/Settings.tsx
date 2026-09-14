import { FormEvent, useEffect, useState } from "react";
import { getJSON, sendJSON } from "../api";

export default function Settings() {
  const [items, setItems] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState("");

  function load() {
    getJSON<Record<string, string>>("/api/settings").then(setItems);
  }

  useEffect(() => {
    load();
  }, []);

  async function onSave(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    for (const [key, value] of fd.entries()) {
      await sendJSON(`/api/settings/${key}`, "PUT", { value: String(value) });
    }
    setMsg("已保存");
    load();
  }

  return (
    <div className="page">
      <h1>设置</h1>
      <p className="lead">
        扫描 zoom 上限等键值。scan_max_z_cap 会在发起扫描时截断实际 max_z，并写入扫描记录可核对。
      </p>
      <form className="form" onSubmit={onSave}>
        {Object.entries(items).map(([k, v]) =>
          k === "scan_max_z_cap" ? (
            <label key={k}>
              {k}（扫描 max_z 上限，0–8）
              <input name={k} type="number" min={0} max={8} defaultValue={v} />
            </label>
          ) : (
            <label key={k}>
              {k}
              <input name={k} defaultValue={v} />
            </label>
          )
        )}
        <button type="submit">保存</button>
      </form>
      {msg && <p>{msg}</p>}
    </div>
  );
}

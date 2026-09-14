import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getJSON, type ScanRun } from "../api";

export default function ScanDetail() {
  const { id } = useParams();
  const [run, setRun] = useState<ScanRun | null>(null);
  useEffect(() => {
    if (!id) return;
    getJSON<ScanRun>(`/api/scans/${id}`).then(setRun);
  }, [id]);
  if (!run) return <div className="page">加载中…</div>;
  return (
    <div className="page">
      <h1>
        扫描 #{run.id} · {run.layer_slug}
      </h1>
      <p className="lead">
        {run.total} 个问题（缺口 {run.missing} / 错层 {run.y_flip}）
      </p>
      <p className="lead mono">
        scheme={run.scheme} · 请求 z={run.requested_max_z ?? "—"} · 上限 z=
        {run.max_z_cap ?? "—"} · 实际 z={run.max_z}
      </p>
      {run.requested_max_z !== null && run.requested_max_z > run.max_z && (
        <p className="err">
          请求的 max_z={run.requested_max_z} 被截断为 {run.max_z}
          {run.max_z_cap !== null && run.requested_max_z > run.max_z_cap
            ? `（设置 scan_max_z_cap=${run.max_z_cap}）`
            : "（受图层 max_z 限制）"}
          。
        </p>
      )}
      <table>
        <thead>
          <tr>
            <th>类型</th>
            <th>z/x/y</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          {(run.issues || []).map((i, idx) => (
            <tr key={idx}>
              <td>{i.kind}</td>
              <td className="mono">
                <Link
                  to={`/layers/${run.layer_slug}/inspect?z=${i.z}&x=${i.x}&y=${i.y}`}
                >
                  {i.z}/{i.x}/{i.y}
                </Link>
              </td>
              <td>{i.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

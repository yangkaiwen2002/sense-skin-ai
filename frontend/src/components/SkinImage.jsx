import { useState } from "react";
import catalog from "../utils/skinImages.json";
import { Cube } from "@phosphor-icons/react";

// Artwork URLs are from the public ByMykel/CSGO-API catalog (see THIRD_PARTY.md).
export default function SkinImage({ iconUrl, name, className = "" }) {
  const [failedUrl, setFailedUrl] = useState(null);
  const src = Object.hasOwn(catalog, name)
    ? catalog[name]
    : iconUrl?.startsWith("https://")
      ? iconUrl
      : iconUrl
        ? `https://community.fastly.steamstatic.com/economy/image/${iconUrl}/360fx360f`
        : null;
  return (
    <div className={`skin-art ${className}`}>
      {src && failedUrl !== src ? (
        <img
          src={src}
          alt={name || "饰品"}
          loading="lazy"
          onError={() => setFailedUrl(src)}
        />
      ) : (
        <div className="skin-art-empty">
          <Cube size={32} weight="light" />
          <span>暂无饰品图片</span>
        </div>
      )}
    </div>
  );
}

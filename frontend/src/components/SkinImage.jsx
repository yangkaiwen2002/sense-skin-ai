/**
 * Skin image with a styled placeholder fallback.
 * Shows Steam CDN image if icon_url is available, otherwise a dark CS2-style placeholder.
 */

const RARITY_COLORS = {
  '违禁': '#e4ae39',
  '隐秘': '#eb4b4b',
  '保密': '#d32ce6',
  '受限': '#8847ff',
  '军规': '#4b69ff',
  '精工': '#5e98d9',
  '消费级': '#b0b0b0',
}

const WEAPON_ABBR = {
  '步枪': 'AR',
  '狙击枪': 'SNP',
  '手枪': 'PST',
  '刀': 'KNF',
  '霰弹枪': 'SHT',
  '冲锋枪': 'SMG',
  '机枪': 'MG',
  '手套': 'GLV',
}

export default function SkinImage({ iconUrl, weaponType, rarity, skinName, size = 'md' }) {
  const rarityColor = RARITY_COLORS[rarity] || '#4a8ef5'
  const abbr = WEAPON_ABBR[weaponType] || (weaponType?.[0] || '?')

  const dims = {
    sm: { w: '100%', h: 100, fontSize: 28, labelSize: 10 },
    md: { w: '100%', h: 180, fontSize: 42, labelSize: 12 },
    lg: { w: '100%', h: 260, fontSize: 56, labelSize: 13 },
  }[size] || { w: '100%', h: 180, fontSize: 42, labelSize: 12 }

  if (iconUrl) {
    const cdnUrl = iconUrl.startsWith('http')
      ? iconUrl
      : `https://community.cloudflare.steamstatic.com/economy/image/${iconUrl}`
    return (
      <div
        style={{
          width: dims.w,
          height: dims.h,
          background: 'linear-gradient(160deg, #0e1420 0%, #0a0f1a 100%)',
          borderRadius: 8,
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(ellipse at center, ${rarityColor}15 0%, transparent 70%)`,
          }}
        />
        <img
          src={cdnUrl}
          alt={skinName || weaponType}
          style={{ maxWidth: '85%', maxHeight: '85%', objectFit: 'contain', position: 'relative' }}
          onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }}
        />
        <Placeholder abbr={abbr} rarityColor={rarityColor} skinName={skinName} fontSize={dims.fontSize} labelSize={dims.labelSize} style={{ display: 'none' }} />
      </div>
    )
  }

  return (
    <div
      style={{
        width: dims.w,
        height: dims.h,
        background: 'linear-gradient(160deg, #0e1420 0%, #0a0f1a 100%)',
        borderRadius: 8,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <Placeholder abbr={abbr} rarityColor={rarityColor} skinName={skinName} fontSize={dims.fontSize} labelSize={dims.labelSize} />
    </div>
  )
}

function Placeholder({ abbr, rarityColor, skinName, fontSize, labelSize, style = {} }) {
  return (
    <div style={{ textAlign: 'center', position: 'relative', zIndex: 1, ...style }}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(ellipse at center, ${rarityColor}18 0%, transparent 65%)`,
          transform: 'scale(3)',
        }}
      />
      <div
        style={{
          fontSize,
          fontWeight: 900,
          letterSpacing: '-0.02em',
          color: rarityColor,
          opacity: 0.7,
          textShadow: `0 0 40px ${rarityColor}60`,
          lineHeight: 1,
          fontFamily: 'monospace',
        }}
      >
        {abbr}
      </div>
      {skinName && (
        <div
          style={{
            fontSize: labelSize,
            color: 'rgba(255,255,255,0.3)',
            marginTop: 8,
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
          }}
        >
          {skinName}
        </div>
      )}
    </div>
  )
}

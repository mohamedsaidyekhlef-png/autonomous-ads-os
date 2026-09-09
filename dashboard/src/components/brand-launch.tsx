import Image from "next/image";

export function BrandLaunch() {
  return (
    <div className="brand-launch" aria-hidden="true">
      <div className="brand-launch-stage">
        <div className="brand-orbit brand-orbit-blue" />
        <div className="brand-orbit brand-orbit-orange" />

        <div className="brand-launch-glow" />

        <Image
          src="/brand-logo.png"
          alt=""
          width={520}
          height={520}
          priority
          className="brand-launch-logo"
        />

        <div className="brand-launch-name">
          <span>Autonomous</span>
          <strong>Ads OS</strong>
        </div>

        <div className="brand-launch-progress">
          <span />
        </div>
      </div>
    </div>
  );
}

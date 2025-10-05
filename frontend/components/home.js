import Link from "next/link";

const navigation = [
  { name: "Home", href: "/" },
  { name: "Dashboard", href: "/dashboard" },
];

export default function home() {
  return (
    <div className="bg-white">
      <main>
        {/* Hero section */}
        <div className="relative overflow-hidden">
          <div
            className="absolute inset-0"
            style={{
              background:
                "linear-gradient(135deg, #0A0E27 0%, #002157 50%, #0B3D91 100%)",
            }}
          >
            <div
              className="absolute inset-0 opacity-20"
              style={{
                backgroundImage:
                  "url(https://images.unsplash.com/photo-1451187580459-43490279c0fa?ixlib=rb-4.0.3&auto=format&fit=crop&w=2072&q=80)",
                backgroundSize: "cover",
                backgroundPosition: "center",
              }}
            />
          </div>

          <div className="relative mx-auto max-w-7xl px-6 py-24 sm:py-32 lg:px-8">
            {/* NASA Space Apps Badge */}
            <div className="flex justify-center mb-8">
              <div
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full"
                style={{
                  backgroundColor: "rgba(252, 61, 33, 0.1)",
                  border: "1px solid #FC3D21",
                }}
              >
                <span
                  className="text-sm font-semibold"
                  style={{ color: "#FC3D21" }}
                >
                  🚀 2025 NASA Space Apps Challenge
                </span>
              </div>
            </div>

            <h1 className="text-center text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
              <span className="block text-white mb-2">
                From EarthData to Action
              </span>
              <span
                className="block text-transparent bg-clip-text"
                style={{
                  background:
                    "linear-gradient(135deg, #7AB6E8 0%, #FFFFFF 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                }}
              >
                Predicting Cleaner, Safer Skies
              </span>
            </h1>

            <p className="mx-auto mt-6 max-w-3xl text-center text-lg text-gray-300 leading-relaxed">
              Fisher-X is an innovative web app developed for NASA&apos;s 2025 Space
              Apps Challenge that forecasts air quality across North America by
              integrating OpenAQ ground-based data and Metostat weather
              information. The platform provides users with real-time
              air-quality insights, alerts, and visualizations to support
              healthier communities and informed decision-making. (TEMPO
              satellite integration is part of our future scope, pending access
              to NASA&apos;s TEMPO data platform.
            </p>

            <div className="flex justify-center">
              <div className="mt-10">
                <Link
                  href="/dashboard"
                  className="flex items-center justify-center rounded-md px-6 py-3 text-base font-medium text-white shadow-lg hover:shadow-xl transition-all"
                  style={{ backgroundColor: "#FC3D21" }}
                >
                  View Dashboard
                </Link>
              </div>
            </div>

            {/* Stats/Key Info */}
            <div className="mt-20 grid grid-cols-1 gap-8 sm:grid-cols-3">
              <div className="text-center">
                <div
                  className="text-4xl font-bold"
                  style={{ color: "#7AB6E8" }}
                >
                  99%
                </div>
                <div className="mt-2 text-sm text-gray-300">
                  of people breathe air exceeding WHO guidelines
                </div>
              </div>
              <div className="text-center">
                <div
                  className="text-4xl font-bold"
                  style={{ color: "#7AB6E8" }}
                >
                  Real-time
                </div>
                <div className="mt-2 text-sm text-gray-300">
                  TEMPO satellite data monitoring
                </div>
              </div>
              <div className="text-center">
                <div
                  className="text-4xl font-bold"
                  style={{ color: "#7AB6E8" }}
                >
                  Oct 4-5
                </div>
                <div className="mt-2 text-sm text-gray-300">
                  2025 Hackathon Event
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* About Section */}
        <div id="about" className="py-24 bg-white">
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="mx-auto max-w-3xl text-center">
              <h2
                className="text-3xl font-bold tracking-tight sm:text-4xl"
                style={{ color: "#0B3D91" }}
              >
                About the Challenge
              </h2>
              <p className="mt-6 text-lg leading-8 text-gray-600">
                The NASA TEMPO mission (Tropospheric Emissions: Monitoring of
                Pollution) is transforming how we monitor and understand air
                quality. The 2025 NASA Space Apps Challenge invites innovators
                to build tools that combine Earth observation data with
                cloud-based technologies to forecast and visualize pollution
                levels. Fisher-X responds to this challenge by creating a
                data-driven app that brings together multiple data streams —
                satellite, ground, and weather — to deliver localized
                air-quality forecasts and public-health alerts for North
                American users.
              </p>
            </div>

            <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
              <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
                <div className="flex flex-col">
                  <dt
                    className="text-base font-semibold leading-7"
                    style={{ color: "#0B3D91" }}
                  >
                    <div
                      className="mb-6 flex h-10 w-10 items-center justify-center rounded-lg"
                      style={{ backgroundColor: "#0B3D91" }}
                    >
                      <span className="text-white text-xl">🛰️</span>
                    </div>
                    Integrate Diverse Data
                  </dt>
                  <dd className="mt-1 flex flex-auto flex-col text-base leading-7 text-gray-600">
                    <p className="flex-auto">
                      Combine OpenAQ ground-based measurements, Metostat weather
                      data, and soon TEMPO satellite products into a unified
                      forecasting system.
                    </p>
                  </dd>
                </div>

                <div className="flex flex-col">
                  <dt
                    className="text-base font-semibold leading-7"
                    style={{ color: "#0B3D91" }}
                  >
                    <div
                      className="mb-6 flex h-10 w-10 items-center justify-center rounded-lg"
                      style={{ backgroundColor: "#0B3D91" }}
                    >
                      <span className="text-white text-xl">📊</span>
                    </div>
                    Forecast & Visualize
                  </dt>
                  <dd className="mt-1 flex flex-auto flex-col text-base leading-7 text-gray-600">
                    <p className="flex-auto">
                      Generate localized air-quality forecasts and provide
                      intuitive charts showing pollutant trends and risk levels.
                    </p>
                  </dd>
                </div>

                <div className="flex flex-col">
                  <dt
                    className="text-base font-semibold leading-7"
                    style={{ color: "#0B3D91" }}
                  >
                    <div
                      className="mb-6 flex h-10 w-10 items-center justify-center rounded-lg"
                      style={{ backgroundColor: "#0B3D91" }}
                    >
                      <span className="text-white text-xl">🔔</span>
                    </div>
                    Alert & Protect
                  </dt>
                  <dd className="mt-1 flex flex-auto flex-col text-base leading-7 text-gray-600">
                    <p className="flex-auto">
                      Send real-time alerts when air quality exceeds safe
                      thresholds, empowering users to reduce exposure.
                    </p>
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>

        {/* Challenge Details Section */}
        <div
          id="challenge"
          className="py-24"
          style={{ backgroundColor: "#F3F4F6" }}
        >
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="mx-auto max-w-3xl">
              <h2
                className="text-3xl font-bold tracking-tight sm:text-4xl mb-8"
                style={{ color: "#0B3D91" }}
              >
                Challenge Details
              </h2>

              <div className="space-y-6">
                <div
                  className="bg-white p-6 rounded-lg shadow-sm border-l-4"
                  style={{ borderLeftColor: "#FC3D21" }}
                >
                  <h3
                    className="text-xl font-semibold mb-3"
                    style={{ color: "#0B3D91" }}
                  >
                    Background
                  </h3>
                  <p className="text-gray-700 leading-relaxed">
                    According to the World Health Organization, 99% of the
                    global population breathes air exceeding safe pollution
                    limits, contributing to millions of premature deaths each
                    year. The causes of air pollution range from traffic and
                    industrial emissions to wildfires and dust storms. To
                    improve prediction and awareness, NASA&apos;s TEMPO satellite
                    provides high-resolution measurements of atmospheric
                    pollutants over North America. By combining this data with
                    ground-based sensors (OpenAQ) and meteorological inputs
                    (Metostat), Fisher-X aims to forecast air quality, identify
                    pollution hotspots, and issue timely health alerts.
                  </p>
                </div>

                <div
                  className="bg-white p-6 rounded-lg shadow-sm border-l-4"
                  style={{ borderLeftColor: "#0B3D91" }}
                >
                  <h3
                    className="text-xl font-semibold mb-3"
                    style={{ color: "#0B3D91" }}
                  >
                    Difficulty Level
                  </h3>
                  <div className="flex gap-2">
                    <span
                      className="px-3 py-1 rounded-full text-sm font-medium"
                      style={{ backgroundColor: "#7AB6E8", color: "white" }}
                    >
                      Intermediate
                    </span>
                    <span
                      className="px-3 py-1 rounded-full text-sm font-medium"
                      style={{ backgroundColor: "#0B3D91", color: "white" }}
                    >
                      Advanced
                    </span>
                  </div>
                </div>

                <div
                  className="bg-white p-6 rounded-lg shadow-sm border-l-4"
                  style={{ borderLeftColor: "#7AB6E8" }}
                >
                  <h3
                    className="text-xl font-semibold mb-3"
                    style={{ color: "#0B3D91" }}
                  >
                    Key Subjects
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {[
                      "AI & Machine Learning",
                      "Data Analysis",
                      "Earth Science",
                      "Forecasting",
                      "Pollution",
                      "Weather",
                      "Web Development",
                    ].map((subject) => (
                      <span
                        key={subject}
                        className="px-3 py-1 rounded-md text-sm"
                        style={{ backgroundColor: "#F3F4F6", color: "#0B3D91" }}
                      >
                        {subject}
                      </span>
                    ))}
                  </div>
                </div>

                <div
                  className="bg-white p-6 rounded-lg shadow-sm border-l-4"
                  style={{ borderLeftColor: "#7AB6E8" }}
                >
                  <h3
                    className="text-xl font-semibold mb-3"
                    style={{ color: "#0B3D91" }}
                  >
                    Project Goals
                  </h3>
                  <p className="text-gray-700 leading-relaxed">
                    Fisher-X&apos;s goal is to create a scalable cloud-based platform
                    for near-real-time air-quality forecasting in North America.
                    Our model currently integrates OpenAQ and Metostat datasets
                    to predict local air-quality index (AQI) values.
                  </p>
                  <p className="text-gray-700 leading-relaxed mt-3">
                    In future iterations, we plan to incorporate NASA TEMPO
                    satellite data for enhanced spatial and temporal accuracy —
                    improving public-health forecasting and policy applications.
                  </p>
                </div>

                <div
                  className="bg-white p-6 rounded-lg shadow-sm border-l-4"
                  style={{ borderLeftColor: "#FC3D21" }}
                >
                  <h3
                    className="text-xl font-semibold mb-3"
                    style={{ color: "#0B3D91" }}
                  >
                    Target Stakeholders
                  </h3>
                  <ul className="space-y-2 text-gray-700">
                    <li className="flex items-start">
                      <span className="mr-2" style={{ color: "#FC3D21" }}>
                        •
                      </span>
                      <span>
                        <strong>Health-Sensitive Groups:</strong> Individuals
                        with respiratory conditions, school administrators, and
                        elder-care providers seeking timely air-quality alerts.
                      </span>
                    </li>
                    <li className="flex items-start">
                      <span className="mr-2" style={{ color: "#FC3D21" }}>
                        •
                      </span>
                      <span>
                        <strong>Policy Partners:</strong> Environmental
                        agencies, local governments, and transportation
                        authorities needing actionable air-quality insights.
                      </span>
                    </li>
                    <li className="flex items-start">
                      <span className="mr-2" style={{ color: "#FC3D21" }}>
                        •
                      </span>
                      <span>
                        <strong>Emergency Response:</strong> Wildfire management
                        and disaster-response teams monitoring pollution spread.
                      </span>
                    </li>
                    <li className="flex items-start">
                      <span className="mr-2" style={{ color: "#FC3D21" }}>
                        •
                      </span>
                      <span>
                        <strong>Community Engagement:</strong> Citizen
                        scientists, educators, and advocacy groups promoting
                        clean-air awareness.
                      </span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Important Notice */}
        <div className="py-16" style={{ backgroundColor: "#0B3D91" }}>
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="text-center">
              <p className="text-lg font-medium text-white">
                The 2025 NASA Space Apps Challenge will take place as scheduled
                on <span className="font-bold">October 4–5, 2025</span>.
              </p>
              <p className="mt-4 text-base text-white">
                Fisher-X participates under the challenge{" "}
                <span className="font-semibold">
                  &quot;From EarthData to Action – Predicting Cleaner, Safer Skies.&quot;
                </span>
              </p>
              <p className="mt-4 text-sm text-gray-300">
                NASA Space Apps is funded by NASA&apos;s Earth Science Division
                through a contract with Booz Allen Hamilton, Mindgrub, and
                SecondMuse.
              </p>
            </div>
          </div>
        </div>
      </main>

      <footer
        aria-labelledby="footer-heading"
        className="mt-0"
        style={{ backgroundColor: "#1E1E1E" }}
      >
        <h2 id="footer-heading" className="sr-only">
          Footer
        </h2>
        <div className="mx-auto max-w-7xl px-6 py-12 lg:px-8">
          <div
            className="border-t pt-8 md:flex md:items-center md:justify-between"
            style={{ borderTopColor: "#374151" }}
          >
            <nav className="flex space-x-6 md:order-2">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className="text-sm text-gray-400 hover:text-white transition-colors"
                >
                  {item.name}
                </Link>
              ))}
            </nav>
            <p className="mt-8 text-base text-gray-400 md:order-1 md:mt-0">
              &copy; 2025 Fisher-X | NASA Space Apps Challenge
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

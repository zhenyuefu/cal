import { getDictionary, Locale } from "@/lib/get-dictionary";
import HomeClient from "@/app/home-client";

export default async function Page({ params }: { params: Promise<{ locale: Locale }> }) {
  const { locale } = await params;
  const loc = locale || "zh";
  const dict = await getDictionary(loc);
  return <HomeClient dict={dict} locale={loc} />;
}

export function generateStaticParams() {
  return [{ locale: "zh" }, { locale: "fr" }];
}

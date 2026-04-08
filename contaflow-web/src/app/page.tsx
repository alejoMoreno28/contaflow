import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import SocialProof from "@/components/SocialProof";
import Problem from "@/components/Problem";
import HowItWorks from "@/components/HowItWorks";
import Feature from "@/components/Feature";
import Pricing from "@/components/Pricing";
import FAQ from "@/components/FAQ";
import CTA from "@/components/CTA";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <main className="min-h-screen">
      <Navbar />
      <Hero />
      <SocialProof />
      <Problem />
      <HowItWorks />
      <Feature />
      <Pricing />
      <FAQ />
      <CTA />
      <Footer />
    </main>
  );
}

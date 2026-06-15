"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { api } from "@/lib/api";
import { useFetch } from "@/lib/useFetch";
import type { Account } from "@/lib/types";
import { Skeleton } from "@/components/ui/LoadingSkeleton";
import { ErrorState } from "@/components/system/StateViews";
import { AccountFeature } from "@/components/account/AccountFeature";

function DetailSkeleton() {
  return (
    <div>
      <Skeleton className="h-3 w-40" />
      <Skeleton className="mt-4 h-16 w-3/4" />
      <Skeleton className="mt-3 h-3 w-56" />
      <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <Skeleton className="h-56 w-full" />
          <Skeleton className="mt-6 h-32 w-full" />
        </div>
        <div className="lg:col-span-4">
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    </div>
  );
}

export default function AccountDetailPage() {
  const params = useParams<{ domain: string }>();
  const domain = decodeURIComponent(params.domain);

  const { data, error, loading, reload } = useFetch<Account>(
    () => api.getAccount(domain),
    [domain],
  );

  return (
    <div className="mx-auto max-w-screen-xl px-4 py-8">
      <Link
        href="/accounts"
        className="inline-flex items-center gap-1 font-mono text-xs uppercase tracking-widest text-neutral-500 transition-colors hover:text-accent"
      >
        <ArrowLeft className="h-4 w-4 stroke-1" /> Back to The Index
      </Link>

      <div className="mt-6">
        {loading && <DetailSkeleton />}
        {!loading && error && <ErrorState message={error} onRetry={reload} />}
        {!loading && !error && data && <AccountFeature account={data} />}
      </div>
    </div>
  );
}

"use client";

import React from "react";
import useSWR from "swr";

interface Data {
	team: string;
	image?: string;
	members: string;
	log_losses: { [key: string]: number };
	predictions: { [key: string]: number };
	avg_log_loss: number;
}

const fetcher = (url: string): Promise<Data[]> =>
	fetch(url).then((res) => res.json());

export default function Home() {
	const { data, isLoading, isValidating, error } = useSWR(
		`${process.env.NEXT_PUBLIC_API_URL}/data`,
		fetcher
	);

	return (
		<main className="p-5 md:p-10">
			<h1 className="text-center font-bold text-xl md:text-3xl">
				2024 MBHS NCAA March Madness Mania
			</h1>
			{isLoading && (
				<p className="text-center font-bold mt-10">Loading Data...</p>
			)}
			{!isLoading && data && (
				<div className="flex flex-col gap-3 md:gap-5 mt-5 md:mt-10">
					{data.map((d, i) => (
						<div
							key={i}
							className="border-2 border-black bg-red-300 rounded-l-full rounded-r-md"
						>
							<div className="flex justify-between flex-wrap">
								<div className="flex gap-3 md:gap-5 items-center">
									<p className="font-bold text-xl md:text-3xl pl-5">#{i + 1}</p>
									<img
										src={d.image}
										alt={`{d.team} image`}
										className="h-24 w-24 md:w-36 object-cover border-l-2 border-r-2 border-black"
									/>
									<div>
										<h2 className="font-bold text-sm md:text-base">{d.team}</h2>
										<p className="text-xs md:text-sm">{d.members}</p>
										<p className="text-sm md:text-base">
											Avg Log Loss:{" "}
											<span className="font-bold">
												{d.avg_log_loss.toFixed(4)}
											</span>
										</p>
									</div>
								</div>
								<div className="hidden xl:flex">
									<div className="h-24 w-80 pt-1 pb-1 overflow-auto border-l-2 border-black pl-2">
										<h3 className="font-bold">Predictions</h3>
										{Object.entries(d.predictions).map(([key, value]) => (
											<p key={key} className="text-sm">
												{key}: {(value * 100).toFixed(2)}%
											</p>
										))}
									</div>
									<div className="h-24 w-80 pt-1 pb-1 overflow-auto border-l-2 border-black pl-2">
										<h3 className="font-bold">Log Losses</h3>
										{Object.entries(d.log_losses).map(([key, value]) => (
											<p key={key} className="text-sm">
												{key}: {value.toFixed(4)}
											</p>
										))}
									</div>
								</div>
							</div>
						</div>
					))}
				</div>
			)}
		</main>
	);
}

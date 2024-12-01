import os
import asyncio
import zlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tqdm import tqdm
import time

class FileSplitter:
    def __init__(self, file_path, output_dir, first_layer_size=1 * 1024 ** 3, chunk_size=500 * 1024, progress_callback=None):
        self.file_path = file_path
        self.output_dir = Path(output_dir)
        self.first_layer_size = first_layer_size
        self.chunk_size = chunk_size
        self.metadata_file = self.output_dir / f"{Path(self.file_path).name}.metadata.json"
        self.progress = 0
        self.pool = ThreadPoolExecutor()
        self.total_size = os.path.getsize(self.file_path)
        self.processed_size = 0
        self.progress_callback = progress_callback
        self.start_time = None

        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)

    def __del__(self):
        self.pool.shutdown()

    def _read_file_chunk(self, start, size):
        with open(self.file_path, "rb") as f:
            f.seek(start)
            return f.read(size)

    def _compress_and_save_chunk(self, chunk_data, chunk_id):
        compressed_data = zlib.compress(chunk_data)
        chunk_file = self.output_dir / f"{Path(self.file_path).name}_chunk_{chunk_id}.bin"
        with open(chunk_file, "wb") as f:
            f.write(compressed_data)
        self.processed_size += len(chunk_data)
        self.progress = (self.processed_size / self.total_size) * 100
        if self.progress_callback:
            self.progress_callback(self.progress, chunk_file.name, len(compressed_data))
        return chunk_file.name, len(compressed_data)

    async def _process_first_layer_chunk(self, start, size, chunk_id):
        tasks = []
        loop = asyncio.get_event_loop()
        for i in range(0, size, self.chunk_size):
            sub_chunk = self._read_file_chunk(start + i, min(self.chunk_size, size - i))
            tasks.append(loop.run_in_executor(self.pool, self._compress_and_save_chunk, sub_chunk, f"{chunk_id}_{i}"))
        return await asyncio.gather(*tasks)

    def _load_metadata(self):
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        return {"file_name": self.file_path, "chunks": []}

    def _save_metadata(self, metadata):
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f)

    async def split(self):
        self.start_time = time.time()
        file_size = self.total_size
        metadata = self._load_metadata()
        completed_chunks = {chunk[0] for chunk in metadata["chunks"]}

        tasks = []
        pbar = tqdm(total=file_size, desc="Splitting File", unit="B", unit_scale=True)

        for i in range(0, file_size, self.first_layer_size):
            layer_size = min(self.first_layer_size, file_size - i)
            layer_id = i // self.first_layer_size

            if any(f"{layer_id}_" in chunk for chunk in completed_chunks):
                pbar.update(layer_size)
                continue

            result = await self._process_first_layer_chunk(i, layer_size, layer_id)
            metadata["chunks"].extend(result)
            self._save_metadata(metadata)
            pbar.update(layer_size)

        pbar.close()
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        speed = self.total_size / elapsed_time
        print(f"文件切割完成！元数据保存在：{self.metadata_file}")
        print(f"耗时: {elapsed_time:.2f} 秒, 平均速度: {speed:.2f} 字节/秒")
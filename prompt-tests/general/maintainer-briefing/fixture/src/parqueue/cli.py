from __future__ import annotations

import json

import click

from .queue import Queue


@click.group()
@click.option("--root", default=".parqueue", show_default=True)
@click.pass_context
def main(ctx: click.Context, root: str) -> None:
    ctx.obj = Queue(root)


@main.command()
@click.argument("payload")
@click.pass_obj
def put(q: Queue, payload: str) -> None:
    click.echo(q.put(json.loads(payload)))


@main.command()
@click.pass_obj
def drain(q: Queue) -> None:
    for item in q.drain():
        click.echo(json.dumps(item))

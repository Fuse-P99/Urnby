# Builtin
import datetime
import json

# External
import discord
from discord.ext import commands

# Internal
import static.common as com
import data.databaseapi as db
from views.ClearOutView import ClearOutView
from checks.IsAdmin import is_admin, NotAdmin
from checks.IsCommandChannel import is_command_channel, NotCommandChannel
from checks.IsMemberVisible import is_member_visible, NotMemberVisible
from checks.IsMember import is_member, NotMember
from checks.IsInDev import is_in_dev, InDevelopment

class Tod(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        print('Initilization on tod complete')

    @commands.Cog.listener()
    async def on_ready(self):
        missing_tables = await db.check_tables(['tod'])
        if missing_tables:
            print(f"Warning, ToD reports missing the following tables in db: {missing_tables}")
    
    @commands.slash_command(name='todnow', description='Simplified tod, takes required parameter of minutes ago')
    async def _tod_now(self, ctx, ago: discord.Option(int, name='minutes_ago', description="Minutes since tod, can be 0" , required=True)):
        now = com.get_current_datetime()
            
        tod_datetime = now - datetime.timedelta(minutes=ago)
            
        rec = {
               "mob": 'Drusella Sathir', 
               "tod_timestamp": tod_datetime.timestamp(), 
               "submitted_timestamp": now.timestamp(), 
               "submitted_by_id": ctx.author.id,
               "_DEBUG_submitted_datetime": now.isoformat(), 
               "_DEBUG_submitted_by": ctx.author.display_name, 
               "_DEBUG_tod_datetime": tod_datetime.isoformat(), 
               }
        row = await db.store_tod(ctx.guild.id, rec)
        await ctx.send_response(content=f"Set tod at {rec['_DEBUG_tod_datetime']} UTC, <t:{int(tod_datetime.timestamp())}>. Drusella will spawn @: <t:{int((tod_datetime+datetime.timedelta(days=1)).timestamp())}>")
        return
        
    @commands.slash_command(name='settod', description='Set tod to a more specific time, with optional parameter for yesterday')
    async def _settod(self, ctx, 
                       tod: discord.Option(str, name='tod', description="Use when time is not 'now' - 24hour clock time UTC (ex 14:49)" , default='now'),
                       mobname: discord.Option(str, name='mobname', default='Drusella Sathir'),
                       daybefore: discord.Option(bool, name='daybefore', description='Use if the tod was actually yesterday',  default=False)):
        now = com.get_current_datetime()
        tod_datetime = {}
        if tod == 'now':
            tod_datetime = now
        if not tod_datetime and len(tod) == 4:
            tod = '0' + tod
        
        offset = 0
        if daybefore:
            offset = -1
            
        if not tod_datetime:    
            tod_datetime = com.datetime_combine((now.date()+datetime.timedelta(days=offset)).isoformat(), tod)
        
        if tod_datetime.second or tod_datetime.microsecond:
            exact = True
        else:
            exact = False
        
        rec = {
               "mob": mobname, 
               "exact": exact,
               "tod_timestamp": tod_datetime.timestamp(), 
               "submitted_timestamp": now.timestamp(), 
               "submitted_by_id": ctx.author.id,
               "_DEBUG_submitted_datetime": now.isoformat(), 
               "_DEBUG_submitted_by": ctx.author.display_name, 
               "_DEBUG_tod_datetime": tod_datetime.isoformat(), 
               }
        row = await db.store_tod(ctx.guild.id, rec)
        await ctx.send_response(content=f"Set tod at {rec['_DEBUG_tod_datetime']} UTC, <t:{int(tod_datetime.timestamp())}>. Drusella will spawn @: <t:{int((tod_datetime+datetime.timedelta(days=1)).timestamp())}>")
        return
    
    @commands.slash_command(name='tod', description='Get current ToD record')
    async def _get_tod(self, ctx):
        rec = await db.get_tod(ctx.guild.id)
        now = com.get_current_datetime()
        hours_till = com.get_hours_from_secs((com.datetime_from_timestamp(rec['tod_timestamp'])+datetime.timedelta(days=1)).timestamp() - now.timestamp())
       
        time_difference = (com.datetime_from_timestamp(rec['tod_timestamp']) + datetime.timedelta(days=1)) - now
        hours, remainder = divmod(time_difference.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_time = f"{hours:2}h {minutes:2}m {seconds:2}s"

        if not hours_till:
            await ctx.send_response(content=f"Last ToD was {rec['_DEBUG_tod_datetime']} unknown upcoming spawn", ephemeral=True)
            return
        await ctx.send_response(content=f"Last ToD Input was by <@{rec['submitted_by_id']}> - {rec['_DEBUG_tod_datetime']} UTC.\n {rec['mob']} will spawn @ <t:{int((com.datetime_from_timestamp(rec['tod_timestamp']) + datetime.timedelta(days=1)).timestamp())}> - in {formatted_time}", ephemeral=False)

async def time_delta_to_minutes(delta:datetime.timedelta) -> float:
    secs = delta.total_seconds()
    sec_to_min = 60
    mins = secs/sec_to_min
    return mins

def setup(bot):
    bot.add_cog(Tod(bot))
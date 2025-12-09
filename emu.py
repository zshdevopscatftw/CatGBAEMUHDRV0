#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           CatEMU 4K GBA                                      ║
║                    Developed by Team Flames / Samsoft                        ║
║                           Version 1.0                                        ║
║  Pure Python 3.13+ GBA Emulator - No external dependencies                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import struct, time, json, zlib
from collections import deque
from dataclasses import dataclass
from typing import Callable
from enum import IntEnum, IntFlag
from pathlib import Path

GBA_WIDTH, GBA_HEIGHT, SCALE = 240, 160, 3
CYCLES_PER_SCANLINE, SCANLINES_PER_FRAME, VISIBLE_SCANLINES = 1232, 228, 160
BIOS_SIZE, EWRAM_SIZE, IWRAM_SIZE = 0x4000, 0x40000, 0x8000
PALETTE_SIZE, VRAM_SIZE, OAM_SIZE, SRAM_SIZE = 0x400, 0x18000, 0x400, 0x10000

class Mem(IntEnum):
    BIOS=0;EWRAM=2;IWRAM=3;IO=4;PALETTE=5;VRAM=6;OAM=7;ROM0=8;ROM0H=9;ROM1=10;ROM1H=11;ROM2=12;ROM2H=13;SRAM=14
class IO(IntEnum):
    DISPCNT=0;DISPSTAT=4;VCOUNT=6;BG0CNT=8;BG1CNT=10;BG2CNT=12;BG3CNT=14;BG0HOFS=16;BG0VOFS=18;BG1HOFS=20;BG1VOFS=22;BG2HOFS=24;BG2VOFS=26;BG3HOFS=28;BG3VOFS=30;KEYINPUT=0x130;IE=0x200;IF=0x202;IME=0x208
class Key(IntFlag):
    A=1;B=2;SELECT=4;START=8;RIGHT=16;LEFT=32;UP=64;DOWN=128;R=256;L=512
class IRQ(IntFlag):
    VBLANK=1;HBLANK=2;VCOUNT=4
class Mode(IntEnum):
    USR=0x10;FIQ=0x11;IRQ=0x12;SVC=0x13;ABT=0x17;UND=0x1B;SYS=0x1F
class Cond(IntEnum):
    EQ=0;NE=1;CS=2;CC=3;MI=4;PL=5;VS=6;VC=7;HI=8;LS=9;GE=10;LT=11;GT=12;LE=13;AL=14

class MMU:
    def __init__(self):
        self.bios=bytearray(BIOS_SIZE);self.ewram=bytearray(EWRAM_SIZE);self.iwram=bytearray(IWRAM_SIZE)
        self.io_ram=bytearray(0x400);self.palette=bytearray(PALETTE_SIZE);self.vram=bytearray(VRAM_SIZE)
        self.oam=bytearray(OAM_SIZE);self.rom=bytearray();self.sram=bytearray(SRAM_SIZE)
        self.bios_readable=True;struct.pack_into('<I',self.bios,0,0xEA00001E);struct.pack_into('<I',self.bios,0x80,0xE3A00302);struct.pack_into('<I',self.bios,0x84,0xE12FFF10)
    def load_rom(self,data):self.rom=bytearray(data);s=len(self.rom);self.rom.extend(bytes((1<<(s-1).bit_length())-s)) if s&(s-1) else None
    def load_bios(self,data):self.bios=bytearray(data[:BIOS_SIZE])
    def read8(self,a):
        r=(a>>24)&0xFF
        if r==Mem.BIOS:return self.bios[a&0x3FFF] if self.bios_readable else 0
        if r==Mem.EWRAM:return self.ewram[a&0x3FFFF]
        if r==Mem.IWRAM:return self.iwram[a&0x7FFF]
        if r==Mem.IO:return self.io_ram[a&0x3FF]
        if r==Mem.PALETTE:return self.palette[a&0x3FF]
        if r==Mem.VRAM:o=a&0x1FFFF;return self.vram[o-0x8000 if o>=VRAM_SIZE else o]
        if r==Mem.OAM:return self.oam[a&0x3FF]
        if r in(Mem.ROM0,Mem.ROM0H,Mem.ROM1,Mem.ROM1H,Mem.ROM2,Mem.ROM2H):o=a&0x1FFFFFF;return self.rom[o] if o<len(self.rom) else 0xFF
        if r==Mem.SRAM:return self.sram[a&0xFFFF]
        return 0xFF
    def read16(self,a):a&=~1;return self.read8(a)|(self.read8(a+1)<<8)
    def read32(self,a):a&=~3;return self.read8(a)|(self.read8(a+1)<<8)|(self.read8(a+2)<<16)|(self.read8(a+3)<<24)
    def write8(self,a,v):
        v&=0xFF;r=(a>>24)&0xFF
        if r==Mem.EWRAM:self.ewram[a&0x3FFFF]=v
        elif r==Mem.IWRAM:self.iwram[a&0x7FFF]=v
        elif r==Mem.IO:self.io_ram[a&0x3FF]=v
        elif r==Mem.PALETTE:x=a&0x3FE;self.palette[x]=self.palette[x+1]=v
        elif r==Mem.VRAM:o=a&0x1FFFF;o=o-0x8000 if o>=VRAM_SIZE else o;x=o&~1;self.vram[x]=self.vram[x+1]=v
        elif r==Mem.SRAM:self.sram[a&0xFFFF]=v
    def write16(self,a,v):a&=~1;v&=0xFFFF;self.write8(a,v&0xFF);self.write8(a+1,(v>>8)&0xFF)
    def write32(self,a,v):a&=~3;v&=0xFFFFFFFF;self.write8(a,v&0xFF);self.write8(a+1,(v>>8)&0xFF);self.write8(a+2,(v>>16)&0xFF);self.write8(a+3,(v>>24)&0xFF)
    def get_io16(self,r):return self.io_ram[r]|(self.io_ram[r+1]<<8)
    def set_io16(self,r,v):self.io_ram[r]=v&0xFF;self.io_ram[r+1]=(v>>8)&0xFF

class ARM7TDMI:
    def __init__(self,mmu):
        self.mmu=mmu;self.r=[0]*16;self.r_banked={Mode.FIQ:[0]*7,Mode.SVC:[0]*2,Mode.ABT:[0]*2,Mode.IRQ:[0]*2,Mode.UND:[0]*2}
        self.spsr={Mode.FIQ:0,Mode.SVC:0,Mode.ABT:0,Mode.IRQ:0,Mode.UND:0};self.cpsr=Mode.SVC|0xC0;self.pipeline=[0,0];self.pipeline_valid=False;self.halted=False;self.cycles=0;self.reset()
    def reset(self):
        for i in range(16):self.r[i]=0
        self.cpsr=Mode.SVC|0xC0;self.r[15]=0x08000000;self.pipeline_valid=False;self.halted=False;self.cycles=0;self.flush_pipeline()
    @property
    def pc(self):return self.r[15]
    @pc.setter
    def pc(self,v):self.r[15]=v&0xFFFFFFFF
    @property
    def sp(self):return self.r[13]
    @sp.setter
    def sp(self,v):self.r[13]=v&0xFFFFFFFF
    @property
    def lr(self):return self.r[14]
    @lr.setter
    def lr(self,v):self.r[14]=v&0xFFFFFFFF
    @property
    def thumb(self):return bool(self.cpsr&0x20)
    @thumb.setter
    def thumb(self,v):self.cpsr=(self.cpsr|0x20) if v else (self.cpsr&~0x20)
    @property
    def mode(self):return self.cpsr&0x1F
    @property
    def n_flag(self):return bool(self.cpsr&0x80000000)
    @n_flag.setter
    def n_flag(self,v):self.cpsr=(self.cpsr|0x80000000) if v else (self.cpsr&~0x80000000)
    @property
    def z_flag(self):return bool(self.cpsr&0x40000000)
    @z_flag.setter
    def z_flag(self,v):self.cpsr=(self.cpsr|0x40000000) if v else (self.cpsr&~0x40000000)
    @property
    def c_flag(self):return bool(self.cpsr&0x20000000)
    @c_flag.setter
    def c_flag(self,v):self.cpsr=(self.cpsr|0x20000000) if v else (self.cpsr&~0x20000000)
    @property
    def v_flag(self):return bool(self.cpsr&0x10000000)
    @v_flag.setter
    def v_flag(self,v):self.cpsr=(self.cpsr|0x10000000) if v else (self.cpsr&~0x10000000)
    @property
    def irq_disabled(self):return bool(self.cpsr&0x80)
    def check_condition(self,c):
        if c==Cond.EQ:return self.z_flag
        if c==Cond.NE:return not self.z_flag
        if c==Cond.CS:return self.c_flag
        if c==Cond.CC:return not self.c_flag
        if c==Cond.MI:return self.n_flag
        if c==Cond.PL:return not self.n_flag
        if c==Cond.VS:return self.v_flag
        if c==Cond.VC:return not self.v_flag
        if c==Cond.HI:return self.c_flag and not self.z_flag
        if c==Cond.LS:return not self.c_flag or self.z_flag
        if c==Cond.GE:return self.n_flag==self.v_flag
        if c==Cond.LT:return self.n_flag!=self.v_flag
        if c==Cond.GT:return not self.z_flag and self.n_flag==self.v_flag
        if c==Cond.LE:return self.z_flag or self.n_flag!=self.v_flag
        if c==Cond.AL:return True
        return False
    def flush_pipeline(self):
        self.pipeline_valid=False
        if self.thumb:self.pc&=~1;self.pipeline[0]=self.mmu.read16(self.pc);self.pc+=2;self.pipeline[1]=self.mmu.read16(self.pc);self.pc+=2
        else:self.pc&=~3;self.pipeline[0]=self.mmu.read32(self.pc);self.pc+=4;self.pipeline[1]=self.mmu.read32(self.pc);self.pc+=4
        self.pipeline_valid=True
    def fetch(self):
        i=self.pipeline[0];self.pipeline[0]=self.pipeline[1]
        if self.thumb:self.pipeline[1]=self.mmu.read16(self.pc);self.pc+=2
        else:self.pipeline[1]=self.mmu.read32(self.pc);self.pc+=4
        return i
    def set_nz(self,v):v&=0xFFFFFFFF;self.n_flag=bool(v&0x80000000);self.z_flag=v==0
    def add_with_carry(self,a,b,c):a&=0xFFFFFFFF;b&=0xFFFFFFFF;r=a+b+c;cy=r>0xFFFFFFFF;r&=0xFFFFFFFF;ov=((a^r)&(b^r)&0x80000000)!=0;return r,cy,ov
    def sub_with_carry(self,a,b,c):return self.add_with_carry(a,~b&0xFFFFFFFF,c)
    def barrel_shift(self,v,t,a,c):
        v&=0xFFFFFFFF
        if a==0:return v,c
        if t==0:
            if a>=32:return 0,(v&1) if a==32 else False
            c=bool((v>>(32-a))&1);return(v<<a)&0xFFFFFFFF,c
        if t==1:
            if a>=32:return 0,bool(v&0x80000000) if a==32 else False
            c=bool((v>>(a-1))&1);return v>>a,c
        if t==2:
            if a>=32:return(0xFFFFFFFF,True) if v&0x80000000 else(0,False)
            c=bool((v>>(a-1))&1);return((v>>a)|(0xFFFFFFFF<<(32-a)))&0xFFFFFFFF if v&0x80000000 else v>>a,c
        if t==3:
            a&=31
            if a==0:return(c<<31)|(v>>1),bool(v&1)
            c=bool((v>>(a-1))&1);return((v>>a)|(v<<(32-a)))&0xFFFFFFFF,c
        return v,c
    def execute_arm(self,i):
        cond=(i>>28)&0xF
        if not self.check_condition(cond):self.cycles+=1;return
        if(i&0x0F000000)==0x0F000000:self.software_interrupt()
        elif(i&0x0C000000)==0x00000000:
            if(i&0x0FC000F0)==0x00000090:self.arm_multiply(i)
            elif(i&0x0FFFFFF0)==0x012FFF10:self.arm_bx(i)
            else:self.arm_data_processing(i)
        elif(i&0x0C000000)==0x04000000:self.arm_single_transfer(i)
        elif(i&0x0E000000)==0x08000000:self.arm_block_transfer(i)
        elif(i&0x0E000000)==0x0A000000:self.arm_branch(i)
        else:self.cycles+=1
    def arm_data_processing(self,i):
        imm=bool(i&0x02000000);sf=bool(i&0x00100000);op=(i>>21)&0xF;rn=(i>>16)&0xF;rd=(i>>12)&0xF
        op1=self.r[rn];op1+=4 if rn==15 else 0;c=self.c_flag
        if imm:im=i&0xFF;ro=((i>>8)&0xF)*2;op2,c=self.barrel_shift(im,3,ro,c)
        else:rm=i&0xF;st=(i>>5)&3;sa=(self.r[(i>>8)&0xF]&0xFF) if i&0x10 else((i>>7)&0x1F);op2=self.r[rm];op2+=4 if rm==15 else 0;op2,c=self.barrel_shift(op2,st,sa,c)
        r=0;wr=True
        if op==0:r=op1&op2
        elif op==1:r=op1^op2
        elif op==2:r,c,ov=self.sub_with_carry(op1,op2,1);self.v_flag=ov if sf else self.v_flag
        elif op==3:r,c,ov=self.sub_with_carry(op2,op1,1);self.v_flag=ov if sf else self.v_flag
        elif op==4:r,c,ov=self.add_with_carry(op1,op2,0);self.v_flag=ov if sf else self.v_flag
        elif op==5:r,c,ov=self.add_with_carry(op1,op2,self.c_flag);self.v_flag=ov if sf else self.v_flag
        elif op==6:r,c,ov=self.sub_with_carry(op1,op2,self.c_flag);self.v_flag=ov if sf else self.v_flag
        elif op==7:r,c,ov=self.sub_with_carry(op2,op1,self.c_flag);self.v_flag=ov if sf else self.v_flag
        elif op==8:r=op1&op2;wr=False
        elif op==9:r=op1^op2;wr=False
        elif op==10:r,c,ov=self.sub_with_carry(op1,op2,1);self.v_flag=ov if sf else self.v_flag;wr=False
        elif op==11:r,c,ov=self.add_with_carry(op1,op2,0);self.v_flag=ov if sf else self.v_flag;wr=False
        elif op==12:r=op1|op2
        elif op==13:r=op2
        elif op==14:r=op1&~op2
        elif op==15:r=~op2
        r&=0xFFFFFFFF
        if sf:self.set_nz(r);self.c_flag=c
        if wr:
            self.r[rd]=r
            if rd==15:
                if sf and self.mode in self.spsr:self.cpsr=self.spsr[self.mode]
                self.flush_pipeline()
        self.cycles+=1
    def arm_multiply(self,i):
        acc=bool(i&0x00200000);sf=bool(i&0x00100000);rd=(i>>16)&0xF;rn=(i>>12)&0xF;rs=(i>>8)&0xF;rm=i&0xF
        r=(self.r[rm]*self.r[rs])&0xFFFFFFFF;r=(r+self.r[rn])&0xFFFFFFFF if acc else r
        self.r[rd]=r;self.set_nz(r) if sf else None;self.cycles+=2
    def arm_branch(self,i):
        link=bool(i&0x01000000);off=i&0x00FFFFFF;off|=0xFF000000 if off&0x00800000 else 0;off=(off<<2)&0xFFFFFFFF;off-=0x100000000 if off&0x80000000 else 0
        self.lr=(self.pc-4)&0xFFFFFFFF if link else self.lr;self.pc=(self.pc+off)&0xFFFFFFFF;self.flush_pipeline();self.cycles+=3
    def arm_bx(self,i):rm=i&0xF;a=self.r[rm];self.thumb=bool(a&1);self.pc=a&~1;self.flush_pipeline();self.cycles+=3
    def arm_single_transfer(self,i):
        imm=not bool(i&0x02000000);pre=bool(i&0x01000000);up=bool(i&0x00800000);byte=bool(i&0x00400000);wb=bool(i&0x00200000);load=bool(i&0x00100000);rn=(i>>16)&0xF;rd=(i>>12)&0xF
        base=self.r[rn];base+=4 if rn==15 else 0
        if imm:off=i&0xFFF
        else:rm=i&0xF;st=(i>>5)&3;sa=(i>>7)&0x1F;off,_=self.barrel_shift(self.r[rm],st,sa,self.c_flag)
        off=-off if not up else off;addr=base;addr=(base+off)&0xFFFFFFFF if pre else addr
        if load:
            if byte:self.r[rd]=self.mmu.read8(addr)
            else:v=self.mmu.read32(addr);ro=(addr&3)*8;self.r[rd]=((v>>ro)|(v<<(32-ro)))&0xFFFFFFFF
            self.flush_pipeline() if rd==15 else None
        else:v=self.r[rd];v+=4 if rd==15 else 0;self.mmu.write8(addr,v&0xFF) if byte else self.mmu.write32(addr,v)
        addr=(base+off)&0xFFFFFFFF if not pre else addr;self.r[rn]=addr if wb or not pre else self.r[rn];self.cycles+=3 if load else 2
    def arm_block_transfer(self,i):
        pre=bool(i&0x01000000);up=bool(i&0x00800000);wb=bool(i&0x00200000);load=bool(i&0x00100000);rn=(i>>16)&0xF;rl=i&0xFFFF
        base=self.r[rn];cnt=bin(rl).count('1');cnt,rl=(16,0x8000) if cnt==0 else(cnt,rl)
        addr=base+(4 if pre else 0) if up else base-cnt*4+(0 if pre else 4)
        for x in range(16):
            if rl&(1<<x):
                if load:self.r[x]=self.mmu.read32(addr);self.flush_pipeline() if x==15 else None
                else:v=self.r[x];v+=4 if x==15 else 0;self.mmu.write32(addr,v)
                addr+=4
        self.r[rn]=base+cnt*4 if up else base-cnt*4 if wb else self.r[rn];self.cycles+=cnt+2
    def execute_thumb(self,i):
        if(i&0xE000)==0x0000:self.thumb_add_sub(i) if(i&0x1800)==0x1800 else self.thumb_shift(i)
        elif(i&0xE000)==0x2000:self.thumb_imm_op(i)
        elif(i&0xFC00)==0x4000:self.thumb_alu(i)
        elif(i&0xFC00)==0x4400:self.thumb_hi_reg(i)
        elif(i&0xF800)==0x4800:self.thumb_pc_load(i)
        elif(i&0xF200)==0x5000:self.thumb_reg_offset(i)
        elif(i&0xF200)==0x5200:self.thumb_sign_extend(i)
        elif(i&0xE000)==0x6000:self.thumb_imm_offset(i)
        elif(i&0xF000)==0x8000:self.thumb_halfword(i)
        elif(i&0xF000)==0x9000:self.thumb_sp_relative(i)
        elif(i&0xF000)==0xA000:self.thumb_load_addr(i)
        elif(i&0xFF00)==0xB000:self.thumb_sp_offset(i)
        elif(i&0xF600)==0xB400:self.thumb_push_pop(i)
        elif(i&0xF000)==0xC000:self.thumb_multiple(i)
        elif(i&0xF000)==0xD000:self.software_interrupt() if(i&0x0F00)==0x0F00 else self.thumb_cond_branch(i)
        elif(i&0xF800)==0xE000:self.thumb_branch(i)
        elif(i&0xF000)==0xF000:self.thumb_long_branch(i)
        else:self.cycles+=1
    def thumb_shift(self,i):
        op=(i>>11)&3;off=(i>>6)&0x1F;rs=(i>>3)&7;rd=i&7;v=self.r[rs];c=self.c_flag
        if op==0:v,c=self.barrel_shift(v,0,off,c) if off>0 else(v,c)
        elif op==1:v,c=self.barrel_shift(v,1,off if off else 32,c)
        elif op==2:v,c=self.barrel_shift(v,2,off if off else 32,c)
        self.r[rd]=v&0xFFFFFFFF;self.set_nz(v);self.c_flag=c;self.cycles+=1
    def thumb_add_sub(self,i):
        imm=bool(i&0x0400);sub=bool(i&0x0200);rn=(i>>6)&7;rs=(i>>3)&7;rd=i&7
        op1=self.r[rs];op2=rn if imm else self.r[rn]
        r,c,ov=self.sub_with_carry(op1,op2,1) if sub else self.add_with_carry(op1,op2,0)
        self.r[rd]=r;self.set_nz(r);self.c_flag=c;self.v_flag=ov;self.cycles+=1
    def thumb_imm_op(self,i):
        op=(i>>11)&3;rd=(i>>8)&7;im=i&0xFF
        if op==0:self.r[rd]=im;self.set_nz(im)
        elif op==1:r,c,ov=self.sub_with_carry(self.r[rd],im,1);self.set_nz(r);self.c_flag=c;self.v_flag=ov
        elif op==2:r,c,ov=self.add_with_carry(self.r[rd],im,0);self.r[rd]=r;self.set_nz(r);self.c_flag=c;self.v_flag=ov
        elif op==3:r,c,ov=self.sub_with_carry(self.r[rd],im,1);self.r[rd]=r;self.set_nz(r);self.c_flag=c;self.v_flag=ov
        self.cycles+=1
    def thumb_alu(self,i):
        op=(i>>6)&0xF;rs=(i>>3)&7;rd=i&7;op1=self.r[rd];op2=self.r[rs];r=0;c=self.c_flag
        if op==0:r=op1&op2
        elif op==1:r=op1^op2
        elif op==2:r,c=self.barrel_shift(op1,0,op2&0xFF,c)
        elif op==3:r,c=self.barrel_shift(op1,1,op2&0xFF,c)
        elif op==4:r,c=self.barrel_shift(op1,2,op2&0xFF,c)
        elif op==5:r,c,ov=self.add_with_carry(op1,op2,self.c_flag);self.v_flag=ov
        elif op==6:r,c,ov=self.sub_with_carry(op1,op2,self.c_flag);self.v_flag=ov
        elif op==7:r,c=self.barrel_shift(op1,3,op2&0xFF,c)
        elif op==8:r=op1&op2;self.set_nz(r);self.cycles+=1;return
        elif op==9:r,c,ov=self.sub_with_carry(0,op2,1);self.v_flag=ov
        elif op==10:r,c,ov=self.sub_with_carry(op1,op2,1);self.set_nz(r);self.c_flag=c;self.v_flag=ov;self.cycles+=1;return
        elif op==11:r,c,ov=self.add_with_carry(op1,op2,0);self.set_nz(r);self.c_flag=c;self.v_flag=ov;self.cycles+=1;return
        elif op==12:r=op1|op2
        elif op==13:r=(op1*op2)&0xFFFFFFFF;self.cycles+=1
        elif op==14:r=op1&~op2
        elif op==15:r=~op2
        r&=0xFFFFFFFF;self.r[rd]=r;self.set_nz(r);self.c_flag=c;self.cycles+=1
    def thumb_hi_reg(self,i):
        op=(i>>8)&3;h1=bool(i&0x80);h2=bool(i&0x40);rs=((i>>3)&7)+(8 if h2 else 0);rd=(i&7)+(8 if h1 else 0)
        if op==0:self.r[rd]=(self.r[rd]+self.r[rs])&0xFFFFFFFF;self.flush_pipeline() if rd==15 else None
        elif op==1:r,c,ov=self.sub_with_carry(self.r[rd],self.r[rs],1);self.set_nz(r);self.c_flag=c;self.v_flag=ov
        elif op==2:self.r[rd]=self.r[rs];self.flush_pipeline() if rd==15 else None
        elif op==3:a=self.r[rs];self.thumb=bool(a&1);self.pc=a&~1;self.flush_pipeline()
        self.cycles+=1
    def thumb_pc_load(self,i):rd=(i>>8)&7;off=(i&0xFF)*4;addr=((self.pc-2)&~3)+off;self.r[rd]=self.mmu.read32(addr);self.cycles+=3
    def thumb_reg_offset(self,i):
        load=bool(i&0x0800);byte=bool(i&0x0400);ro=(i>>6)&7;rb=(i>>3)&7;rd=i&7;addr=(self.r[rb]+self.r[ro])&0xFFFFFFFF
        if load:self.r[rd]=self.mmu.read8(addr) if byte else self.mmu.read32(addr)
        else:self.mmu.write8(addr,self.r[rd]&0xFF) if byte else self.mmu.write32(addr,self.r[rd])
        self.cycles+=3 if load else 2
    def thumb_sign_extend(self,i):
        h=bool(i&0x0800);s=bool(i&0x0400);ro=(i>>6)&7;rb=(i>>3)&7;rd=i&7;addr=(self.r[rb]+self.r[ro])&0xFFFFFFFF
        if not h and not s:self.mmu.write16(addr,self.r[rd]&0xFFFF);self.cycles+=2
        elif not h and s:v=self.mmu.read8(addr);v|=0xFFFFFF00 if v&0x80 else 0;self.r[rd]=v;self.cycles+=3
        elif h and not s:self.r[rd]=self.mmu.read16(addr);self.cycles+=3
        else:v=self.mmu.read16(addr);v|=0xFFFF0000 if v&0x8000 else 0;self.r[rd]=v;self.cycles+=3
    def thumb_imm_offset(self,i):
        byte=bool(i&0x1000);load=bool(i&0x0800);off=(i>>6)&0x1F;rb=(i>>3)&7;rd=i&7;off*=1 if byte else 4;addr=(self.r[rb]+off)&0xFFFFFFFF
        if load:self.r[rd]=self.mmu.read8(addr) if byte else self.mmu.read32(addr)
        else:self.mmu.write8(addr,self.r[rd]&0xFF) if byte else self.mmu.write32(addr,self.r[rd])
        self.cycles+=3 if load else 2
    def thumb_halfword(self,i):
        load=bool(i&0x0800);off=((i>>6)&0x1F)*2;rb=(i>>3)&7;rd=i&7;addr=(self.r[rb]+off)&0xFFFFFFFF
        self.r[rd]=self.mmu.read16(addr) if load else None;self.mmu.write16(addr,self.r[rd]&0xFFFF) if not load else None;self.cycles+=3 if load else 2
    def thumb_sp_relative(self,i):
        load=bool(i&0x0800);rd=(i>>8)&7;off=(i&0xFF)*4;addr=(self.sp+off)&0xFFFFFFFF
        self.r[rd]=self.mmu.read32(addr) if load else None;self.mmu.write32(addr,self.r[rd]) if not load else None;self.cycles+=3 if load else 2
    def thumb_load_addr(self,i):sp=bool(i&0x0800);rd=(i>>8)&7;off=(i&0xFF)*4;self.r[rd]=(self.sp+off)&0xFFFFFFFF if sp else(((self.pc-2)&~3)+off)&0xFFFFFFFF;self.cycles+=1
    def thumb_sp_offset(self,i):neg=bool(i&0x80);off=(i&0x7F)*4;self.sp=(self.sp-off if neg else self.sp+off)&0xFFFFFFFF;self.cycles+=1
    def thumb_push_pop(self,i):
        load=bool(i&0x0800);pclr=bool(i&0x0100);rl=i&0xFF;cnt=bin(rl).count('1')+(1 if pclr else 0)
        if load:
            addr=self.sp
            for x in range(8):
                if rl&(1<<x):self.r[x]=self.mmu.read32(addr);addr+=4
            if pclr:self.pc=self.mmu.read32(addr)&~1;addr+=4;self.flush_pipeline()
            self.sp=addr
        else:
            addr=self.sp-cnt*4;self.sp=addr
            for x in range(8):
                if rl&(1<<x):self.mmu.write32(addr,self.r[x]);addr+=4
            if pclr:self.mmu.write32(addr,self.lr)
        self.cycles+=cnt+2
    def thumb_multiple(self,i):
        load=bool(i&0x0800);rb=(i>>8)&7;rl=i&0xFF;addr=self.r[rb];cnt=bin(rl).count('1')
        for x in range(8):
            if rl&(1<<x):self.r[x]=self.mmu.read32(addr) if load else None;self.mmu.write32(addr,self.r[x]) if not load else None;addr+=4
        self.r[rb]=addr if not(load and(rl&(1<<rb))) else self.r[rb];self.cycles+=cnt+2
    def thumb_cond_branch(self,i):
        cond=(i>>8)&0xF;off=i&0xFF;off|=0xFFFFFF00 if off&0x80 else 0;off=((off<<1)+0x100000000)&0xFFFFFFFF;off-=0x100000000 if off>=0x80000000 else 0
        if self.check_condition(cond):self.pc=(self.pc+off)&0xFFFFFFFF;self.flush_pipeline();self.cycles+=3
        else:self.cycles+=1
    def thumb_branch(self,i):off=i&0x7FF;off|=0xFFFFF800 if off&0x400 else 0;off=((off<<1)+0x100000000)&0xFFFFFFFF;off-=0x100000000 if off>=0x80000000 else 0;self.pc=(self.pc+off)&0xFFFFFFFF;self.flush_pipeline();self.cycles+=3
    def thumb_long_branch(self,i):
        h=bool(i&0x0800);off=i&0x7FF
        if not h:off|=0xFFFFF800 if off&0x400 else 0;self.lr=(self.pc+(off<<12))&0xFFFFFFFF;self.cycles+=1
        else:t=self.pc-2;self.pc=(self.lr+(off<<1))&0xFFFFFFFE;self.lr=t|1;self.flush_pipeline();self.cycles+=3
    def software_interrupt(self):
        oc=self.cpsr;self.cpsr=(self.cpsr&~0x1F)|Mode.SVC|0x80;self.spsr[Mode.SVC]=oc;self.lr=self.pc-(2 if self.thumb else 4);self.thumb=False;self.pc=0x08;self.flush_pipeline();self.cycles+=3
    def check_irq(self):
        if self.irq_disabled:return False
        ime=self.mmu.get_io16(IO.IME);ie=self.mmu.get_io16(IO.IE);iff=self.mmu.get_io16(IO.IF)
        if ime and(ie&iff):
            oc=self.cpsr;self.cpsr=(self.cpsr&~0x3F)|Mode.IRQ|0x80;self.spsr[Mode.IRQ]=oc;self.lr=self.pc-(2 if oc&0x20 else 4)+4;self.thumb=False;self.pc=0x18;self.flush_pipeline();self.halted=False;return True
        return False
    def step(self):
        if self.halted:return 1
        if not self.pipeline_valid:self.flush_pipeline()
        self.cycles=0;i=self.fetch();self.execute_thumb(i) if self.thumb else self.execute_arm(i);return self.cycles if self.cycles>0 else 1

class PPU:
    PALETTES={'gba':None,'original_gameboy':[(155,188,15),(139,172,15),(48,98,48),(15,56,15)],'gba_sp':[(248,248,248),(176,176,176),(104,104,104),(32,32,32)],'pink_dreams':[(255,218,233),(255,145,175),(199,80,120),(99,30,60)],'ocean_blue':[(224,248,255),(128,200,248),(48,128,200),(16,56,128)],'amber_glow':[(255,224,168),(248,176,88),(192,112,32),(96,48,0)]}
    def __init__(self,mmu):self.mmu=mmu;self.framebuffer=bytearray(GBA_WIDTH*GBA_HEIGHT*3);self.scanline=[0]*GBA_WIDTH;self.layer_buffers=[[0x8000]*GBA_WIDTH for _ in range(6)];self.layer_priority=[[4]*GBA_WIDTH for _ in range(6)];self.layer_enable=[True]*8;self.palette_filter='gba'
    def rgb15_to_rgb24(self,c):return((c&0x1F)<<3,((c>>5)&0x1F)<<3,((c>>10)&0x1F)<<3)
    def apply_palette_filter(self,r,g,b):
        if self.palette_filter=='gba' or self.palette_filter not in self.PALETTES:return r,g,b
        p=self.PALETTES[self.palette_filter];return(r,g,b) if p is None else p[min(3,(r*299+g*587+b*114)//1000//64)]
    def get_bg_pixel(self,bg,x,y):
        bgc=self.mmu.get_io16(IO.BG0CNT+bg*2);cb=((bgc>>2)&3)*0x4000;sb=((bgc>>8)&0x1F)*0x800;cm=bool(bgc&0x80);ss=(bgc>>14)&3
        ho=self.mmu.get_io16(IO.BG0HOFS+bg*4)&0x1FF;vo=self.mmu.get_io16(IO.BG0VOFS+bg*4)&0x1FF
        w,h=[(256,256),(512,256),(256,512),(512,512)][ss];px=(x+ho)%w;py=(y+vo)%h;tx=px//8;ty=py//8;pixelx=px%8;pixely=py%8
        sbl=0;sbl+=(tx//32) if w==512 else 0;tx%=32 if w==512 else tx;sbl+=(ty//32)*(2 if w==512 else 1) if h==512 else 0;ty%=32 if h==512 else ty
        ta=sb+sbl*0x800+(ty*32+tx)*2;te=self.mmu.vram[ta]|(self.mmu.vram[ta+1]<<8);tn=te&0x3FF;hf=bool(te&0x400);vf=bool(te&0x800);pn=(te>>12)&0xF
        pixelx=7-pixelx if hf else pixelx;pixely=7-pixely if vf else pixely
        if cm:to=tn*64+pixely*8+pixelx;ci=self.mmu.vram[cb+to];return 0x8000 if ci==0 else self.mmu.palette[ci*2]|(self.mmu.palette[ci*2+1]<<8)
        else:to=tn*32+pixely*4+pixelx//2;b=self.mmu.vram[cb+to];ci=(b>>4) if pixelx&1 else(b&0xF);return 0x8000 if ci==0 else self.mmu.palette[pn*32+ci*2]|(self.mmu.palette[pn*32+ci*2+1]<<8)
    def render_sprites(self,y):
        for x in range(GBA_WIDTH):self.layer_buffers[4][x]=0x8000;self.layer_priority[4][x]=4
        if not self.layer_enable[4]:return
        dc=self.mmu.get_io16(IO.DISPCNT);om=bool(dc&0x40)
        for i in range(127,-1,-1):
            oa=i*8;a0=self.mmu.oam[oa]|(self.mmu.oam[oa+1]<<8);a1=self.mmu.oam[oa+2]|(self.mmu.oam[oa+3]<<8);a2=self.mmu.oam[oa+4]|(self.mmu.oam[oa+5]<<8)
            if((a0>>8)&3)==2:continue
            sy=a0&0xFF;sy-=256 if sy>=160 else 0;sh=(a0>>14)&3;sz=(a1>>14)&3;szs=[[(8,8),(16,16),(32,32),(64,64)],[(16,8),(32,8),(32,16),(64,32)],[(8,16),(8,32),(16,32),(32,64)],[(8,8),(8,8),(8,8),(8,8)]];w,h=szs[sh][sz]
            if y<sy or y>=sy+h:continue
            sx=a1&0x1FF;sx-=512 if sx>=240 else 0;hf=bool(a1&0x1000);vf=bool(a1&0x2000);tn=a2&0x3FF;pr=(a2>>10)&3;pn=(a2>>12)&0xF;cm=bool(a0&0x2000)
            sl=y-sy;sl=h-1-sl if vf else sl
            for px in range(w):
                scx=sx+px
                if scx<0 or scx>=GBA_WIDTH:continue
                if self.layer_priority[4][scx]<pr:continue
                tpx=w-1-px if hf else px;tr=sl//8;tc=tpx//8;pixelx=tpx%8;pixely=sl%8
                ti=tn+tr*(w//8)*(2 if cm else 1)+tc*(2 if cm else 1) if om else(tn+tc*(2 if cm else 1))+tr*32
                ob=0x10000
                if cm:off=ti*32+pixely*8+pixelx;ci=self.mmu.vram[ob+off] if ob+off<VRAM_SIZE else 0;po=0x200+ci*2 if ci else None
                else:off=ti*32+pixely*4+pixelx//2;b=self.mmu.vram[ob+off] if ob+off<VRAM_SIZE else 0;ci=(b>>4) if pixelx&1 else(b&0xF);po=0x200+pn*32+ci*2 if ci else None
                if po is None:continue
                c=self.mmu.palette[po]|(self.mmu.palette[po+1]<<8);self.layer_buffers[4][scx]=c;self.layer_priority[4][scx]=pr
    def render_scanline(self,y):
        dc=self.mmu.get_io16(IO.DISPCNT);mode=dc&7;bd=self.mmu.palette[0]|(self.mmu.palette[1]<<8)
        for l in range(6):
            for x in range(GBA_WIDTH):self.layer_buffers[l][x]=0x8000;self.layer_priority[l][x]=4
        for x in range(GBA_WIDTH):self.layer_buffers[5][x]=bd;self.layer_priority[5][x]=4
        if mode==0:
            for bg in range(4):
                if(dc&(0x100<<bg)) and self.layer_enable[bg]:
                    bgc=self.mmu.get_io16(IO.BG0CNT+bg*2);pr=bgc&3
                    for x in range(GBA_WIDTH):c=self.get_bg_pixel(bg,x,y);self.layer_buffers[bg][x]=c if c!=0x8000 else self.layer_buffers[bg][x];self.layer_priority[bg][x]=pr if c!=0x8000 else self.layer_priority[bg][x]
        elif mode==3:
            if self.layer_enable[2]:
                for x in range(GBA_WIDTH):off=(y*GBA_WIDTH+x)*2;c=self.mmu.vram[off]|(self.mmu.vram[off+1]<<8);self.layer_buffers[2][x]=c;self.layer_priority[2][x]=0
        elif mode==4:
            if self.layer_enable[2]:
                fr=0xA000 if dc&0x10 else 0
                for x in range(GBA_WIDTH):off=fr+y*GBA_WIDTH+x;ci=self.mmu.vram[off];c=self.mmu.palette[ci*2]|(self.mmu.palette[ci*2+1]<<8) if ci>0 else 0x8000;self.layer_buffers[2][x]=c if c!=0x8000 else self.layer_buffers[2][x];self.layer_priority[2][x]=0 if c!=0x8000 else self.layer_priority[2][x]
        if dc&0x1000:self.render_sprites(y)
        for x in range(GBA_WIDTH):
            bc=self.layer_buffers[5][x];bp=4
            for l in[0,1,2,3,4]:
                if self.layer_buffers[l][x]!=0x8000 and self.layer_priority[l][x]<=bp:bp=self.layer_priority[l][x];bc=self.layer_buffers[l][x]
            self.scanline[x]=bc
        fbo=y*GBA_WIDTH*3
        for x in range(GBA_WIDTH):r,g,b=self.rgb15_to_rgb24(self.scanline[x]);r,g,b=self.apply_palette_filter(r,g,b);self.framebuffer[fbo+x*3]=r;self.framebuffer[fbo+x*3+1]=g;self.framebuffer[fbo+x*3+2]=b

@dataclass
class Cheat:
    name:str;code:str;enabled:bool=True;cheat_type:str="raw"

class CheatEngine:
    def __init__(self,mmu):self.mmu=mmu;self.cheats=[]
    def add_cheat(self,n,c,t="raw"):self.cheats.append(Cheat(name=n,code=c,cheat_type=t))
    def remove_cheat(self,i):self.cheats.pop(i) if 0<=i<len(self.cheats) else None
    def toggle_cheat(self,i):self.cheats[i].enabled=not self.cheats[i].enabled if 0<=i<len(self.cheats) else None
    def apply_cheats(self):
        for c in self.cheats:
            if c.enabled:
                for l in c.code.strip().upper().replace('-','').split('\n'):
                    l=l.strip()
                    if not l:continue
                    if c.cheat_type=="gameshark":self._gs(l)
                    elif c.cheat_type=="codebreaker":self._cb(l)
                    else:self._raw(l)
    def _raw(self,l):
        try:p=l.split(':');a=int(p[0],16);v=int(p[1],16);self.mmu.write8(a,v) if v<=0xFF else(self.mmu.write16(a,v) if v<=0xFFFF else self.mmu.write32(a,v))
        except:pass
    def _gs(self,l):
        try:p=l.split();c1=int(p[0],16);c2=int(p[1],16);ct=(c1>>24)&0xFF;a=c1&0x00FFFFFF;a+=0x02000000 if a<0x02000000 else 0;self.mmu.write8(a,c2&0xFF) if ct==0 else(self.mmu.write16(a,c2&0xFFFF) if ct==1 else(self.mmu.write32(a,c2) if ct==2 else None))
        except:pass
    def _cb(self,l):
        try:p=l.split();c1=int(p[0],16);c2=int(p[1],16);ct=(c1>>28)&0xF;a=c1&0x0FFFFFFF;self.mmu.write32(a,c2) if ct==0 else(self.mmu.write16(a,c2&0xFFFF) if ct==1 else(self.mmu.write8(a,c2&0xFF) if ct==2 else None))
        except:pass

class SaveStateManager:
    def __init__(self,emu):self.emu=emu;self.states={};self.rewind_buffer=deque(maxlen=300);self.frame_counter=0
    def save_state(self,s):
        try:self.states[s]=self._capture();return True
        except:return False
    def load_state(self,s):
        if s not in self.states:return False
        try:self._restore(self.states[s]);return True
        except:return False
    def save_to_file(self,s,p):
        if s not in self.states and not self.save_state(s):return False
        try:open(p,'wb').write(zlib.compress(self.states[s]));return True
        except:return False
    def load_from_file(self,p,s):
        try:self.states[s]=zlib.decompress(open(p,'rb').read());return self.load_state(s)
        except:return False
    def update_rewind(self):self.frame_counter+=1;self.rewind_buffer.append(self._capture()) if self.frame_counter>=1 else None;self.frame_counter=0
    def rewind(self,f=1):
        if len(self.rewind_buffer)<f:return False
        for _ in range(f):self.rewind_buffer.pop() if self.rewind_buffer else None
        if self.rewind_buffer:self._restore(self.rewind_buffer[-1]);return True
        return False
    def _capture(self):return zlib.compress(json.dumps({'cpu_r':list(self.emu.cpu.r),'cpu_cpsr':self.emu.cpu.cpsr,'cpu_spsr':{str(k):v for k,v in self.emu.cpu.spsr.items()},'cpu_halted':self.emu.cpu.halted,'ewram':bytes(self.emu.mmu.ewram).hex(),'iwram':bytes(self.emu.mmu.iwram).hex(),'io_ram':bytes(self.emu.mmu.io_ram).hex(),'palette':bytes(self.emu.mmu.palette).hex(),'vram':bytes(self.emu.mmu.vram).hex(),'oam':bytes(self.emu.mmu.oam).hex(),'sram':bytes(self.emu.mmu.sram).hex()}).encode())
    def _restore(self,d):
        s=json.loads(zlib.decompress(d).decode());self.emu.cpu.r=s['cpu_r'];self.emu.cpu.cpsr=s['cpu_cpsr'];self.emu.cpu.spsr={int(k):v for k,v in s['cpu_spsr'].items()};self.emu.cpu.halted=s['cpu_halted'];self.emu.cpu.flush_pipeline()
        self.emu.mmu.ewram=bytearray.fromhex(s['ewram']);self.emu.mmu.iwram=bytearray.fromhex(s['iwram']);self.emu.mmu.io_ram=bytearray.fromhex(s['io_ram']);self.emu.mmu.palette=bytearray.fromhex(s['palette']);self.emu.mmu.vram=bytearray.fromhex(s['vram']);self.emu.mmu.oam=bytearray.fromhex(s['oam']);self.emu.mmu.sram=bytearray.fromhex(s['sram'])

class GBAEmulator:
    def __init__(self):
        self.mmu=MMU();self.cpu=ARM7TDMI(self.mmu);self.ppu=PPU(self.mmu);self.cheats=CheatEngine(self.mmu);self.save_states=SaveStateManager(self)
        self.running=False;self.paused=False;self.rom_loaded=False;self.rom_path="";self.rom_title="";self.scanline=0;self.keys=0x3FF;self.speed_multiplier=1.0;self.turbo=False
    def load_rom(self,p):
        try:
            d=open(p,'rb').read();self.mmu.load_rom(d);self.rom_path=p;self.rom_loaded=True;self.rom_title=d[0xA0:0xAC].decode('ascii',errors='ignore').strip('\x00') if len(d)>=0xAC else Path(p).stem
            sp=Path(p).with_suffix('.sav');self.mmu.sram=bytearray(open(sp,'rb').read()[:SRAM_SIZE]) if sp.exists() else self.mmu.sram;self.reset();return True
        except Exception as e:print(f"Error:{e}");return False
    def load_bios(self,p):
        try:self.mmu.load_bios(open(p,'rb').read());return True
        except:return False
    def save_sram(self):
        if self.rom_path:
            try:open(Path(self.rom_path).with_suffix('.sav'),'wb').write(self.mmu.sram)
            except:pass
    def reset(self):self.cpu.reset();self.scanline=0;self.mmu.set_io16(IO.KEYINPUT,0x3FF);self.mmu.set_io16(IO.DISPCNT,0x0080)
    def key_down(self,k):self.keys&=~k;self.mmu.set_io16(IO.KEYINPUT,self.keys)
    def key_up(self,k):self.keys|=k;self.mmu.set_io16(IO.KEYINPUT,self.keys)
    def step_scanline(self):
        tc=CYCLES_PER_SCANLINE;cr=0
        while cr<tc:self.cpu.check_irq();cr+=self.cpu.step()
        self.mmu.set_io16(IO.VCOUNT,self.scanline);ds=self.mmu.get_io16(IO.DISPSTAT)
        if self.scanline<VISIBLE_SCANLINES:self.ppu.render_scanline(self.scanline);ds|=0x02;self.mmu.set_io16(IO.IF,self.mmu.get_io16(IO.IF)|IRQ.HBLANK) if ds&0x10 else None
        elif self.scanline==VISIBLE_SCANLINES:ds|=0x01;self.mmu.set_io16(IO.IF,self.mmu.get_io16(IO.IF)|IRQ.VBLANK) if ds&0x08 else None;self.cheats.apply_cheats()
        vct=(ds>>8)&0xFF;ds=(ds|0x04) if self.scanline==vct else(ds&~0x04);self.mmu.set_io16(IO.IF,self.mmu.get_io16(IO.IF)|IRQ.VCOUNT) if self.scanline==vct and ds&0x20 else None
        self.mmu.set_io16(IO.DISPSTAT,ds);self.scanline+=1
        if self.scanline>=SCANLINES_PER_FRAME:self.scanline=0;ds&=~0x01;self.mmu.set_io16(IO.DISPSTAT,ds);self.save_states.update_rewind()
    def run_frame(self):
        if not self.rom_loaded or self.paused:return
        for _ in range(SCANLINES_PER_FRAME):self.step_scanline()
    def get_framebuffer(self):return bytes(self.ppu.framebuffer)

class CatGBAApp:
    def __init__(self):
        self.root=tk.Tk();self.root.title("CatEMU 4K GBA - Team Flames / Samsoft");self.root.configure(bg='#1a1a2e')
        self.emu=GBAEmulator();self.scale=SCALE;self.display_width=GBA_WIDTH*self.scale;self.display_height=GBA_HEIGHT*self.scale
        self.target_fps=60;self.last_frame_time=time.time();self.fps_counter=0;self.fps_display=0;self.fps_last_update=time.time();self.running=False
        self.key_map={'x':Key.A,'z':Key.B,'Return':Key.START,'space':Key.SELECT,'Up':Key.UP,'Down':Key.DOWN,'Left':Key.LEFT,'Right':Key.RIGHT,'a':Key.L,'s':Key.R}
        self._create_menu();self._create_main_layout();self._create_bindings();self.photo=None;self._create_display_image();self._update_loop()
    def _create_menu(self):
        mb=tk.Menu(self.root);self.root.config(menu=mb)
        fm=tk.Menu(mb,tearoff=0);mb.add_cascade(label="File",menu=fm);fm.add_command(label="Open ROM...",command=self._open_rom);fm.add_command(label="Load BIOS...",command=self._load_bios);fm.add_separator();fm.add_command(label="Save SRAM",command=lambda:self.emu.save_sram());fm.add_separator();fm.add_command(label="Exit",command=self._on_close)
        em=tk.Menu(mb,tearoff=0);mb.add_cascade(label="Emulation",menu=em);em.add_command(label="Reset",command=self._reset);em.add_command(label="Pause/Resume",command=self._toggle_pause)
        sm=tk.Menu(em,tearoff=0);em.add_cascade(label="Save States",menu=sm)
        for i in range(1,5):sm.add_command(label=f"Save Slot {i}",command=lambda s=i:self._save_state(s));sm.add_command(label=f"Load Slot {i}",command=lambda s=i:self._load_state(s))
        vm=tk.Menu(mb,tearoff=0);mb.add_cascade(label="Video",menu=vm)
        scm=tk.Menu(vm,tearoff=0);vm.add_cascade(label="Scale",menu=scm)
        for s in[1,2,3,4,5]:scm.add_command(label=f"{s}x",command=lambda s=s:self._set_scale(s))
        pm=tk.Menu(vm,tearoff=0);vm.add_cascade(label="Palette",menu=pm)
        for n in PPU.PALETTES.keys():pm.add_command(label=n.replace('_',' ').title(),command=lambda n=n:self._set_palette(n))
        lm=tk.Menu(vm,tearoff=0);vm.add_cascade(label="Layers",menu=lm);self.layer_vars=[]
        for i,n in enumerate(['BG0','BG1','BG2','BG3','OBJ']):v=tk.BooleanVar(value=True);self.layer_vars.append(v);lm.add_checkbutton(label=n,variable=v,command=self._make_layer_toggle(i,v))
        hm=tk.Menu(mb,tearoff=0);mb.add_cascade(label="Help",menu=hm);hm.add_command(label="Controls",command=self._show_controls);hm.add_command(label="About",command=self._show_about)
    def _make_layer_toggle(self,i,v):
        def t():self.emu.ppu.layer_enable[i]=v.get()
        return t
    def _create_main_layout(self):
        self.main_frame=ttk.Frame(self.root);self.main_frame.pack(fill='both',expand=True,padx=5,pady=5)
        self.left_panel=ttk.Frame(self.main_frame);self.left_panel.pack(side='left',fill='both',expand=True)
        self.canvas=tk.Canvas(self.left_panel,width=self.display_width,height=self.display_height,bg='#000000',highlightthickness=2,highlightbackground='#4a4a6a');self.canvas.pack(padx=10,pady=10)
        self.status_frame=ttk.Frame(self.left_panel);self.status_frame.pack(fill='x',padx=10);self.status_label=ttk.Label(self.status_frame,text="No ROM loaded",font=('Consolas',10));self.status_label.pack(side='left');self.fps_label=ttk.Label(self.status_frame,text="FPS: 0",font=('Consolas',10));self.fps_label.pack(side='right')
        self.right_panel=ttk.Frame(self.main_frame,width=280);self.right_panel.pack(side='right',fill='y',padx=5);self.right_panel.pack_propagate(False)
        self.notebook=ttk.Notebook(self.right_panel);self.notebook.pack(fill='both',expand=True);self._create_controls_tab();self._create_cheats_tab();self._create_states_tab()
    def _create_controls_tab(self):
        f=ttk.Frame(self.notebook,padding=10);self.notebook.add(f,text='Controls')
        if_=ttk.LabelFrame(f,text="Game Info",padding=10);if_.pack(fill='x',pady=5);self.game_title_label=ttk.Label(if_,text="Title: -");self.game_title_label.pack(anchor='w');self.game_status_label=ttk.Label(if_,text="Status: Stopped");self.game_status_label.pack(anchor='w')
        cf=ttk.LabelFrame(f,text="Playback",padding=10);cf.pack(fill='x',pady=5);bf=ttk.Frame(cf);bf.pack();ttk.Button(bf,text="Play",command=self._start,width=8).pack(side='left',padx=2);ttk.Button(bf,text="Pause",command=self._toggle_pause,width=8).pack(side='left',padx=2);ttk.Button(bf,text="Reset",command=self._reset,width=8).pack(side='left',padx=2)
        kf=ttk.LabelFrame(f,text="Key Bindings",padding=10);kf.pack(fill='x',pady=5);ttk.Label(kf,text="A:X  B:Z  Start:Enter  Select:Space\nD-Pad:Arrows  L:A  R:S  Turbo:Tab",font=('Consolas',9)).pack()
    def _create_cheats_tab(self):
        f=ttk.Frame(self.notebook,padding=10);self.notebook.add(f,text='Cheats')
        tf=ttk.Frame(f);tf.pack(fill='x',pady=5);ttk.Label(tf,text="Type:").pack(side='left');self.cheat_type_var=tk.StringVar(value="gameshark");ttk.Combobox(tf,textvariable=self.cheat_type_var,values=["raw","gameshark","codebreaker"],state='readonly',width=15).pack(side='left',padx=5)
        inf=ttk.LabelFrame(f,text="Add Cheat",padding=5);inf.pack(fill='x',pady=5);ttk.Label(inf,text="Name:").pack(anchor='w');self.cheat_name_entry=ttk.Entry(inf);self.cheat_name_entry.pack(fill='x');ttk.Label(inf,text="Code:").pack(anchor='w');self.cheat_code_text=tk.Text(inf,height=4,width=30);self.cheat_code_text.pack(fill='x');ttk.Button(inf,text="Add Cheat",command=self._add_cheat).pack(pady=5)
        lf=ttk.LabelFrame(f,text="Active Cheats",padding=5);lf.pack(fill='both',expand=True,pady=5);self.cheat_listbox=tk.Listbox(lf,height=6);self.cheat_listbox.pack(fill='both',expand=True);bf=ttk.Frame(lf);bf.pack(fill='x');ttk.Button(bf,text="Toggle",command=self._toggle_cheat).pack(side='left',padx=2);ttk.Button(bf,text="Remove",command=self._remove_cheat).pack(side='left',padx=2)
    def _create_states_tab(self):
        f=ttk.Frame(self.notebook,padding=10);self.notebook.add(f,text='States')
        qf=ttk.LabelFrame(f,text="Quick Save/Load",padding=10);qf.pack(fill='x',pady=5)
        for i in range(1,5):r=ttk.Frame(qf);r.pack(fill='x',pady=2);ttk.Label(r,text=f"Slot {i}:",width=8).pack(side='left');ttk.Button(r,text="Save",command=lambda s=i:self._save_state(s),width=8).pack(side='left',padx=2);ttk.Button(r,text="Load",command=lambda s=i:self._load_state(s),width=8).pack(side='left',padx=2)
        ff=ttk.LabelFrame(f,text="File Operations",padding=10);ff.pack(fill='x',pady=5);ttk.Button(ff,text="Export State...",command=self._export_state).pack(fill='x',pady=2);ttk.Button(ff,text="Import State...",command=self._import_state).pack(fill='x',pady=2)
        rf=ttk.LabelFrame(f,text="Rewind",padding=10);rf.pack(fill='x',pady=5);ttk.Label(rf,text="Hold Backspace to rewind").pack();self.rewind_enabled_var=tk.BooleanVar(value=True);ttk.Checkbutton(rf,text="Enable Rewind",variable=self.rewind_enabled_var).pack()
    def _create_display_image(self):d=bytes([0]*(GBA_WIDTH*GBA_HEIGHT*3));s=self._scale_framebuffer(d);ppm=f"P6\n{self.display_width} {self.display_height}\n255\n".encode()+s;self.photo=tk.PhotoImage(data=ppm,format='ppm');self.canvas.create_image(0,0,anchor='nw',image=self.photo,tags='display')
    def _scale_framebuffer(self,d):
        if self.scale==1:return d
        s=bytearray(self.display_width*self.display_height*3)
        for y in range(GBA_HEIGHT):
            for x in range(GBA_WIDTH):
                si=(y*GBA_WIDTH+x)*3;r,g,b=d[si],d[si+1],d[si+2]
                for sy in range(self.scale):
                    for sx in range(self.scale):dx=x*self.scale+sx;dy=y*self.scale+sy;di=(dy*self.display_width+dx)*3;s[di]=r;s[di+1]=g;s[di+2]=b
        return bytes(s)
    def _update_display(self):d=self.emu.get_framebuffer();s=self._scale_framebuffer(d);ppm=f"P6\n{self.display_width} {self.display_height}\n255\n".encode()+s;self.photo=tk.PhotoImage(data=ppm,format='ppm');self.canvas.itemconfig('display',image=self.photo)
    def _create_bindings(self):self.root.bind('<KeyPress>',self._on_key_press);self.root.bind('<KeyRelease>',self._on_key_release);self.root.protocol("WM_DELETE_WINDOW",self._on_close);self.root.bind('<Control-o>',lambda e:self._open_rom());self.root.bind('<Control-r>',lambda e:self._reset());self.root.bind('<p>',lambda e:self._toggle_pause());[self.root.bind(f'<F{i}>',lambda e,s=i:self._load_state(s)) for i in range(1,5)];[self.root.bind(f'<Shift-F{i}>',lambda e,s=i:self._save_state(s)) for i in range(1,5)]
    def _on_key_press(self,e):k=e.keysym;self.emu.key_down(self.key_map[k]) if k in self.key_map else None;self.emu.__dict__.__setitem__('turbo',True) if k=='Tab' else None;self.emu.save_states.rewind(5) if k=='BackSpace' and self.rewind_enabled_var.get() else None
    def _on_key_release(self,e):k=e.keysym;self.emu.key_up(self.key_map[k]) if k in self.key_map else None;self.emu.__dict__.__setitem__('turbo',False) if k=='Tab' else None
    def _on_close(self):self.running=False;self.emu.save_sram();self.root.destroy()
    def _update_loop(self):
        if self.running and self.emu.rom_loaded and not self.emu.paused:
            ct=time.time();ti=1.0/(self.target_fps*self.emu.speed_multiplier);ti=0 if self.emu.turbo else ti;el=ct-self.last_frame_time
            if el>=ti or self.emu.turbo:self.emu.run_frame();self._update_display();self.last_frame_time=ct;self.fps_counter+=1
            if ct-self.fps_last_update>=1.0:self.fps_display=self.fps_counter;self.fps_counter=0;self.fps_last_update=ct;self.fps_label.config(text=f"FPS: {self.fps_display}")
        self.root.after(1,self._update_loop)
    def _open_rom(self):
        p=filedialog.askopenfilename(title="Open GBA ROM",filetypes=[("GBA ROMs","*.gba *.bin"),("All","*.*")])
        if p and self.emu.load_rom(p):self.running=True;self.game_title_label.config(text=f"Title: {self.emu.rom_title}");self.game_status_label.config(text="Status: Running");self.status_label.config(text=self.emu.rom_title)
        elif p:messagebox.showerror("Error","Failed to load ROM")
    def _load_bios(self):p=filedialog.askopenfilename(title="Open GBA BIOS",filetypes=[("BIOS","*.bin *.bios"),("All","*.*")]);messagebox.showinfo("Success","BIOS loaded") if p and self.emu.load_bios(p) else(messagebox.showerror("Error","Failed to load BIOS") if p else None)
    def _start(self):self.running=True;self.emu.paused=False;self.game_status_label.config(text="Status: Running") if self.emu.rom_loaded else None
    def _toggle_pause(self):self.emu.paused=not self.emu.paused;self.game_status_label.config(text="Status: "+("Paused" if self.emu.paused else "Running")) if self.emu.rom_loaded else None
    def _reset(self):self.emu.reset()
    def _set_scale(self,s):self.scale=s;self.display_width=GBA_WIDTH*s;self.display_height=GBA_HEIGHT*s;self.canvas.config(width=self.display_width,height=self.display_height);self._create_display_image()
    def _set_palette(self,n):self.emu.ppu.palette_filter=n
    def _save_state(self,s):self.status_label.config(text=f"State saved to slot {s}") if self.emu.save_states.save_state(s) else self.status_label.config(text="Failed to save state")
    def _load_state(self,s):self.status_label.config(text=f"State loaded from slot {s}") if self.emu.save_states.load_state(s) else self.status_label.config(text=f"No state in slot {s}")
    def _export_state(self):p=filedialog.asksaveasfilename(title="Export Save State",defaultextension=".sst",filetypes=[("Save State","*.sst"),("All","*.*")]);messagebox.showinfo("Success","State exported") if p and self.emu.save_states.save_to_file(1,p) else(messagebox.showerror("Error","Failed to export") if p else None)
    def _import_state(self):p=filedialog.askopenfilename(title="Import Save State",filetypes=[("Save State","*.sst"),("All","*.*")]);messagebox.showinfo("Success","State imported") if p and self.emu.save_states.load_from_file(p,1) else(messagebox.showerror("Error","Failed to import") if p else None)
    def _add_cheat(self):n=self.cheat_name_entry.get().strip();c=self.cheat_code_text.get("1.0","end").strip();self.emu.cheats.add_cheat(n,c,self.cheat_type_var.get()) if n and c else None;self._update_cheat_list();self.cheat_name_entry.delete(0,'end');self.cheat_code_text.delete("1.0","end")
    def _toggle_cheat(self):s=self.cheat_listbox.curselection();self.emu.cheats.toggle_cheat(s[0]) if s else None;self._update_cheat_list()
    def _remove_cheat(self):s=self.cheat_listbox.curselection();self.emu.cheats.remove_cheat(s[0]) if s else None;self._update_cheat_list()
    def _update_cheat_list(self):self.cheat_listbox.delete(0,'end');[self.cheat_listbox.insert('end',f"{'[ON]' if c.enabled else '[OFF]'} {c.name}") for c in self.emu.cheats.cheats]
    def _show_controls(self):messagebox.showinfo("Controls","A:X  B:Z\nStart:Enter  Select:Space\nD-Pad:Arrows\nL:A  R:S\nTurbo:Tab\nRewind:Backspace\n\nSave:Shift+F1-F4\nLoad:F1-F4")
    def _show_about(self):messagebox.showinfo("About","CatEMU 4K GBA\n\nDeveloped by Team Flames / Samsoft\nVersion 1.0\n\nPure Python 3.13+ GBA Emulator")
    def run(self):self.root.mainloop()

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           CatEMU 4K GBA                                      ║
║                    Developed by Team Flames / Samsoft                        ║
║                           Version 1.0                                        ║
║  Pure Python 3.13+ GBA Emulator - No external dependencies                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

Controls: A:X  B:Z  Start:Enter  Select:Space  D-Pad:Arrows  L:A  R:S
          Turbo:Tab  Rewind:Backspace  Save:Shift+F1-F4  Load:F1-F4

Starting GUI...
    """)
    CatGBAApp().run()

if __name__=="__main__":main()
